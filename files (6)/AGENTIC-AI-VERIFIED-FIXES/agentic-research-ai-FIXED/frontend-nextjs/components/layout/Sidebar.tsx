'use client'

import { useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
    LayoutDashboard,
    Target,
    Folder,
    Users,
    Settings,
    ChevronLeft,
    ChevronRight,
    Zap
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'

interface NavItem {
    title: string
    href: string
    icon: React.ComponentType<{ className?: string }>
}

const navItems: NavItem[] = [
    {
        title: 'Dashboard',
        href: '/dashboard',
        icon: LayoutDashboard
    },
    {
        title: 'Goals',
        href: '/goals',
        icon: Target
    },
    {
        title: 'Projects',
        href: '/projects',
        icon: Folder
    },
    {
        title: 'Team',
        href: '/team',
        icon: Users
    },
    {
        title: 'Settings',
        href: '/settings',
        icon: Settings
    }
]

export function Sidebar() {
    const pathname = usePathname()
    const [collapsed, setCollapsed] = useState(false)

    return (
        <div
            className={cn(
                'fixed left-0 top-0 z-40 h-screen border-r bg-background transition-all duration-300',
                collapsed ? 'w-16' : 'w-64'
            )}
        >
            <div className="flex h-full flex-col">
                {/* Logo */}
                <div className="flex h-16 items-center border-b px-4">
                    <Link href="/dashboard" className="flex items-center gap-2">
                        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary">
                            <Zap className="h-5 w-5 text-primary-foreground" />
                        </div>
                        {!collapsed && (
                            <span className="font-semibold">Agentic Research</span>
                        )}
                    </Link>
                </div>

                {/* Navigation */}
                <nav className="flex-1 space-y-1 p-4">
                    {navItems.map((item) => {
                        const Icon = item.icon
                        const isActive = pathname === item.href || pathname.startsWith(item.href + '/')

                        return (
                            <Link key={item.href} href={item.href}>
                                <div
                                    className={cn(
                                        'flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors',
                                        'hover:bg-accent hover:text-accent-foreground',
                                        isActive
                                            ? 'bg-primary text-primary-foreground hover:bg-primary/90'
                                            : 'text-muted-foreground'
                                    )}
                                >
                                    <Icon className="h-5 w-5 shrink-0" />
                                    {!collapsed && (
                                        <span className="flex-1">{item.title}</span>
                                    )}
                                </div>
                            </Link>
                        )
                    })}
                </nav>

                {/* Collapse Toggle */}
                <div className="border-t p-4">
                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setCollapsed(!collapsed)}
                        className="w-full justify-start"
                    >
                        {collapsed ? (
                            <ChevronRight className="h-4 w-4" />
                        ) : (
                            <>
                                <ChevronLeft className="h-4 w-4 mr-2" />
                                Collapse
                            </>
                        )}
                    </Button>
                </div>
            </div>
        </div>
    )
}
