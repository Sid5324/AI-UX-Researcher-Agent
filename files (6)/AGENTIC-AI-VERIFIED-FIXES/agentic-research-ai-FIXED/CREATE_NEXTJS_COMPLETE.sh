#!/bin/bash
# Script to create complete Next.js application

echo "Creating Complete Next.js Application..."

mkdir -p frontend-nextjs/{app,components,lib,hooks,styles}
mkdir -p frontend-nextjs/app/\(auth\)/{login,register}
mkdir -p frontend-nextjs/app/\(dashboard\)/{dashboard,projects,team,settings}
mkdir -p frontend-nextjs/components/{ui,auth,project,team}

echo "✅ Directory structure created"
echo "Next: Creating all component files..."

