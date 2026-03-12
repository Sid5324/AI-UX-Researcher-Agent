'use client'

import { useState } from 'react'
import { useAuth } from '@/hooks/useAuth'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useToast } from '@/components/ui/use-toast'

export default function SettingsPage() {
    const { user } = useAuth()
    const { toast } = useToast()
    const [loading, setLoading] = useState(false)
    const [activeTab, setActiveTab] = useState('profile')

    const handleSave = async () => {
        setLoading(true)
        await new Promise(resolve => setTimeout(resolve, 1000))
        setLoading(false)
        toast({
            title: 'Settings saved',
            description: 'Your preferences have been updated.',
        })
    }

    const tabs = [
        { id: 'profile', label: 'Profile' },
        { id: 'preferences', label: 'Preferences' },
        { id: 'notifications', label: 'Notifications' },
        { id: 'api', label: 'API Keys' },
        { id: 'account', label: 'Account' },
    ]

    return (
        <div className="container mx-auto py-8 max-w-4xl">
            <h1 className="text-3xl font-bold mb-2">Settings</h1>
            <p className="text-muted-foreground mb-8">
                Manage your account settings and preferences
            </p>

            <div className="flex gap-6">
                {/* Sidebar */}
                <div className="w-48 space-y-1">
                    {tabs.map((tab) => (
                        <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id)}
                            className={`w-full text-left px-4 py-2 rounded-lg transition-colors ${activeTab === tab.id
                                    ? 'bg-primary text-primary-foreground'
                                    : 'hover:bg-gray-100'
                                }`}
                        >
                            {tab.label}
                        </button>
                    ))}
                </div>

                {/* Content */}
                <div className="flex-1">
                    {activeTab === 'profile' && (
                        <Card>
                            <CardHeader>
                                <CardTitle>Profile Information</CardTitle>
                                <CardDescription>
                                    Update your personal information and public profile
                                </CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div className="space-y-2">
                                    <Label htmlFor="name">Full Name</Label>
                                    <Input id="name" defaultValue={user?.name || ''} />
                                </div>
                                <div className="space-y-2">
                                    <Label htmlFor="email">Email</Label>
                                    <Input id="email" type="email" defaultValue={user?.email || ''} readOnly />
                                </div>
                                <div className="space-y-2">
                                    <Label htmlFor="bio">Bio</Label>
                                    <Input id="bio" placeholder="Tell us about yourself" />
                                </div>
                                <Button onClick={handleSave} disabled={loading}>
                                    {loading ? 'Saving...' : 'Save Changes'}
                                </Button>
                            </CardContent>
                        </Card>
                    )}

                    {activeTab === 'preferences' && (
                        <Card>
                            <CardHeader>
                                <CardTitle>Preferences</CardTitle>
                                <CardDescription>
                                    Customize your experience
                                </CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-6">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <Label className="text-base">Dark Mode</Label>
                                        <p className="text-sm text-muted-foreground">
                                            Use dark theme across the application
                                        </p>
                                    </div>
                                    <input type="checkbox" className="w-5 h-5" />
                                </div>
                                <div className="flex items-center justify-between">
                                    <div>
                                        <Label className="text-base">Auto-save</Label>
                                        <p className="text-sm text-muted-foreground">
                                            Automatically save goal progress
                                        </p>
                                    </div>
                                    <input type="checkbox" className="w-5 h-5" defaultChecked />
                                </div>
                                <div className="space-y-2">
                                    <Label>Language</Label>
                                    <select className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm">
                                        <option value="en">English</option>
                                        <option value="es">Spanish</option>
                                        <option value="fr">French</option>
                                    </select>
                                </div>
                                <Button onClick={handleSave} disabled={loading}>
                                    {loading ? 'Saving...' : 'Save Preferences'}
                                </Button>
                            </CardContent>
                        </Card>
                    )}

                    {activeTab === 'notifications' && (
                        <Card>
                            <CardHeader>
                                <CardTitle>Notifications</CardTitle>
                                <CardDescription>
                                    Choose what notifications you receive
                                </CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-6">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <Label className="text-base">Email Notifications</Label>
                                        <p className="text-sm text-muted-foreground">
                                            Receive updates via email
                                        </p>
                                    </div>
                                    <input type="checkbox" className="w-5 h-5" defaultChecked />
                                </div>
                                <div className="flex items-center justify-between">
                                    <div>
                                        <Label className="text-base">Goal Completion</Label>
                                        <p className="text-sm text-muted-foreground">
                                            Notify when goals are completed
                                        </p>
                                    </div>
                                    <input type="checkbox" className="w-5 h-5" defaultChecked />
                                </div>
                                <div className="flex items-center justify-between">
                                    <div>
                                        <Label className="text-base">Team Activity</Label>
                                        <p className="text-sm text-muted-foreground">
                                            Notify about team member actions
                                        </p>
                                    </div>
                                    <input type="checkbox" className="w-5 h-5" />
                                </div>
                                <Button onClick={handleSave} disabled={loading}>
                                    {loading ? 'Saving...' : 'Save Notification Settings'}
                                </Button>
                            </CardContent>
                        </Card>
                    )}

                    {activeTab === 'api' && (
                        <Card>
                            <CardHeader>
                                <CardTitle>API Keys</CardTitle>
                                <CardDescription>
                                    Manage your API keys for external integrations
                                </CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div className="space-y-2">
                                    <Label>API Key</Label>
                                    <div className="flex gap-2">
                                        <Input value="••••••••••••••••••••••••••" readOnly type="password" />
                                        <Button variant="outline">Copy</Button>
                                    </div>
                                </div>
                                <Button variant="outline">Generate New Key</Button>
                            </CardContent>
                        </Card>
                    )}

                    {activeTab === 'account' && (
                        <Card>
                            <CardHeader>
                                <CardTitle>Account Management</CardTitle>
                                <CardDescription>
                                    Manage your account status
                                </CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div className="flex items-center justify-between p-4 border rounded-lg">
                                    <div>
                                        <h4 className="font-medium">Delete Account</h4>
                                        <p className="text-sm text-muted-foreground">
                                            Permanently delete your account and all data
                                        </p>
                                    </div>
                                    <Button variant="destructive">Delete</Button>
                                </div>
                            </CardContent>
                        </Card>
                    )}
                </div>
            </div>
        </div>
    )
}
