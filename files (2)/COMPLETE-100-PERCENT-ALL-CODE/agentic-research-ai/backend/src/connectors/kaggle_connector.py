"""
Complete Kaggle Connector - Fully Working
==========================================
"""

import asyncio
import aiohttp
import aiofiles
import os
import hashlib
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from backend.src.core.config import get_settings


settings = get_settings()


class KaggleConnector:
    """Production Kaggle connector with caching and profiling."""
    
    def __init__(self):
        self.username = settings.kaggle_username
        self.key = settings.kaggle_key
        self.cache_dir = Path.home() / ".cache" / "agentic-research" / "kaggle"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        if not self.username or not self.key:
            raise ValueError("KAGGLE_USERNAME and KAGGLE_KEY required")
        
        self.base_url = "https://www.kaggle.com/api/v1"
        self.auth = aiohttp.BasicAuth(self.username, self.key)
    
    async def search(
        self,
        query: str,
        max_results: int = 10,
        file_types: List[str] = None,
        min_size_mb: Optional[float] = None,
        max_size_mb: Optional[float] = None,
        sort_by: str = "hotness",
    ) -> Dict[str, Any]:
        """
        Search Kaggle datasets.
        
        Args:
            query: Search query
            max_results: Maximum results to return
            file_types: Filter by file types ["csv", "json", etc]
            min_size_mb: Minimum dataset size in MB
            max_size_mb: Maximum dataset size in MB
            sort_by: Sort order ("hotness", "votes", "updated", "active")
            
        Returns:
            List of datasets with metadata
        """
        url = f"{self.base_url}/datasets/list"
        
        params = {
            "search": query,
            "page": 1,
            "pageSize": max_results,
            "sortBy": sort_by,
        }
        
        if file_types:
            params["fileType"] = ",".join(file_types)
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, auth=self.auth) as response:
                if response.status != 200:
                    return {
                        "success": False,
                        "error": f"Kaggle API error: {response.status}",
                    }
                
                data = await response.json()
                
                # Filter by size if specified
                results = []
                for dataset in data:
                    size_mb = dataset.get("totalBytes", 0) / (1024 * 1024)
                    
                    if min_size_mb and size_mb < min_size_mb:
                        continue
                    if max_size_mb and size_mb > max_size_mb:
                        continue
                    
                    results.append({
                        "ref": dataset["ref"],
                        "title": dataset["title"],
                        "subtitle": dataset.get("subtitle", ""),
                        "size_mb": round(size_mb, 2),
                        "vote_count": dataset.get("voteCount", 0),
                        "download_count": dataset.get("downloadCount", 0),
                        "usability_rating": dataset.get("usabilityRating", 0),
                        "last_updated": dataset.get("lastUpdated", ""),
                        "license": dataset.get("licenseName", ""),
                        "tags": dataset.get("tags", []),
                    })
                
                return {
                    "success": True,
                    "query": query,
                    "count": len(results),
                    "results": results,
                }
    
    async def download(
        self,
        dataset_ref: str,
        force_refresh: bool = False,
    ) -> Dict[str, Any]:
        """
        Download dataset with intelligent caching.
        
        Args:
            dataset_ref: Dataset reference (e.g., "user/dataset-name")
            force_refresh: Force re-download even if cached
            
        Returns:
            Downloaded dataset info with local path
        """
        # Check cache
        cache_path = self.cache_dir / dataset_ref.replace("/", "_")
        cache_path.mkdir(parents=True, exist_ok=True)
        
        metadata_file = cache_path / "metadata.json"
        
        # Load cached metadata
        if metadata_file.exists() and not force_refresh:
            async with aiofiles.open(metadata_file, 'r') as f:
                metadata = json.loads(await f.read())
            
            # Check if cache is fresh (< 7 days old)
            cached_date = datetime.fromisoformat(metadata["cached_at"])
            if datetime.now() - cached_date < timedelta(days=7):
                return {
                    "success": True,
                    "cached": True,
                    "local_path": str(cache_path),
                    "files": metadata["files"],
                    "metadata": metadata,
                }
        
        # Download dataset
        url = f"{self.base_url}/datasets/download/{dataset_ref}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, auth=self.auth) as response:
                if response.status != 200:
                    return {
                        "success": False,
                        "error": f"Download failed: {response.status}",
                    }
                
                # Save zip file
                zip_path = cache_path / "dataset.zip"
                
                async with aiofiles.open(zip_path, 'wb') as f:
                    async for chunk in response.content.iter_chunked(8192):
                        await f.write(chunk)
        
        # Extract zip
        import zipfile
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(cache_path)
        
        # Remove zip
        os.remove(zip_path)
        
        # List files
        files = [str(f.relative_to(cache_path)) for f in cache_path.rglob("*") if f.is_file()]
        
        # Save metadata
        metadata = {
            "dataset_ref": dataset_ref,
            "cached_at": datetime.now().isoformat(),
            "files": files,
            "file_count": len(files),
        }
        
        async with aiofiles.open(metadata_file, 'w') as f:
            await f.write(json.dumps(metadata, indent=2))
        
        return {
            "success": True,
            "cached": False,
            "local_path": str(cache_path),
            "files": files,
            "metadata": metadata,
        }
    
    async def profile(self, local_path: str) -> Dict[str, Any]:
        """
        Profile downloaded dataset.
        
        Analyzes CSV/JSON files to generate data profile.
        """
        import pandas as pd
        
        path = Path(local_path)
        
        # Find data files
        csv_files = list(path.glob("*.csv"))
        json_files = list(path.glob("*.json"))
        
        profiles = []
        
        # Profile CSV files
        for csv_file in csv_files[:5]:  # Limit to first 5 files
            try:
                df = pd.read_csv(csv_file, nrows=10000)
                
                profile = {
                    "file": csv_file.name,
                    "format": "csv",
                    "rows": len(df),
                    "columns": len(df.columns),
                    "column_names": list(df.columns),
                    "column_types": df.dtypes.astype(str).to_dict(),
                    "missing_values": df.isnull().sum().to_dict(),
                    "memory_mb": round(df.memory_usage(deep=True).sum() / (1024 * 1024), 2),
                    "sample": df.head(3).to_dict('records'),
                }
                
                # Add numeric summary
                numeric_cols = df.select_dtypes(include=['number']).columns
                if len(numeric_cols) > 0:
                    profile["numeric_summary"] = df[numeric_cols].describe().to_dict()
                
                profiles.append(profile)
            
            except Exception as e:
                profiles.append({
                    "file": csv_file.name,
                    "error": str(e),
                })
        
        # Profile JSON files
        for json_file in json_files[:5]:
            try:
                async with aiofiles.open(json_file, 'r') as f:
                    data = json.loads(await f.read())
                
                if isinstance(data, list):
                    df = pd.DataFrame(data[:10000])
                    
                    profile = {
                        "file": json_file.name,
                        "format": "json",
                        "rows": len(df),
                        "columns": len(df.columns),
                        "column_names": list(df.columns),
                        "sample": df.head(3).to_dict('records'),
                    }
                    
                    profiles.append(profile)
                else:
                    profile = {
                        "file": json_file.name,
                        "format": "json",
                        "type": type(data).__name__,
                        "keys": list(data.keys()) if isinstance(data, dict) else None,
                    }
                    
                    profiles.append(profile)
            
            except Exception as e:
                profiles.append({
                    "file": json_file.name,
                    "error": str(e),
                })
        
        return {
            "success": True,
            "profiles": profiles,
            "total_files": len(csv_files) + len(json_files),
        }
    
    async def get_dataset_metadata(self, dataset_ref: str) -> Dict[str, Any]:
        """Get detailed metadata for a dataset without downloading."""
        url = f"{self.base_url}/datasets/view/{dataset_ref}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, auth=self.auth) as response:
                if response.status != 200:
                    return {
                        "success": False,
                        "error": f"API error: {response.status}",
                    }
                
                data = await response.json()
                
                return {
                    "success": True,
                    "title": data.get("title"),
                    "description": data.get("description"),
                    "owner": data.get("owner", {}).get("name"),
                    "size_bytes": data.get("totalBytes", 0),
                    "file_count": data.get("totalFiles", 0),
                    "license": data.get("licenseName"),
                    "tags": data.get("tags", []),
                    "created_at": data.get("creationDate"),
                    "updated_at": data.get("lastUpdated"),
                }


# Singleton
_kaggle_connector: Optional[KaggleConnector] = None


def get_kaggle_connector() -> KaggleConnector:
    """Get Kaggle connector singleton."""
    global _kaggle_connector
    
    if _kaggle_connector is None:
        _kaggle_connector = KaggleConnector()
    
    return _kaggle_connector
