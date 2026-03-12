'use client'

import { useConnection } from '@/hooks/useConnection'
import { useEffect, useState } from 'react'

export function ConnectionStatus() {
    const { isOnline, error, checkConnection } = useConnection()
    const [showDetails, setShowDetails] = useState(false)

    // Periodic connection check
    useEffect(() => {
        const interval = setInterval(() => {
            checkConnection()
        }, 30000) // Check every 30 seconds

        return () => clearInterval(interval)
    }, [checkConnection])

    if (isOnline) return null

    return (
        <div className="fixed bottom-4 right-4 z-50">
            <div className="rounded-lg border border-rose-500/50 bg-rose-500/10 p-4 backdrop-blur-sm">
                <div className="flex items-center gap-2">
                    <div className="h-3 w-3 animate-pulse rounded-full bg-rose-500" />
                    <span className="font-medium text-rose-400">Backend Offline</span>
                    <button
                        onClick={() => setShowDetails(!showDetails)}
                        className="ml-2 text-xs text-rose-300 underline"
                    >
                        {showDetails ? 'Hide' : 'Details'}
                    </button>
                </div>
                {showDetails && (
                    <div className="mt-2 max-w-xs text-sm text-rose-300">
                        <p>{error || 'Cannot connect to backend server'}</p>
                        <p className="mt-2 text-xs">
                            Make sure the backend is running on port 8000
                        </p>
                        <button
                            onClick={() => checkConnection()}
                            className="mt-2 rounded bg-rose-500/20 px-3 py-1 text-xs text-rose-300 hover:bg-rose-500/30"
                        >
                            Retry Connection
                        </button>
                    </div>
                )}
            </div>
        </div>
    )
}
