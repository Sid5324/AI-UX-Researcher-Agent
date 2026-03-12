'use client'

import { useState } from 'react'
import { Plus, Mail, MoreHorizontal, User } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'
import { useToast } from '@/components/ui/use-toast'

interface TeamMember {
    id: string
    name: string
    email: string
    role: 'admin' | 'member' | 'viewer'
    status: 'active' | 'pending' | 'inactive'
    avatar?: string
}

export default function TeamPage() {
    const { toast } = useToast()
    const [isInviteOpen, setIsInviteOpen] = useState(false)
    const [newMember, setNewMember] = useState({ email: '', role: 'member' })

    const [members, setMembers] = useState<TeamMember[]>([
        {
            id: '1',
            name: 'You',
            email: 'you@example.com',
            role: 'admin',
            status: 'active',
        },
        {
            id: '2',
            name: 'John Doe',
            email: 'john@example.com',
            role: 'member',
            status: 'active',
        },
        {
            id: '3',
            name: 'Jane Smith',
            email: 'jane@example.com',
            role: 'viewer',
            status: 'pending',
        },
    ])

    const handleInvite = async () => {
        if (!newMember.email) {
            toast({
                title: 'Error',
                description: 'Please enter an email address',
                variant: 'destructive',
            })
            return
        }

        const member: TeamMember = {
            id: Date.now().toString(),
            name: newMember.email.split('@')[0],
            email: newMember.email,
            role: newMember.role as 'admin' | 'member' | 'viewer',
            status: 'pending',
        }

        setMembers([...members, member])
        setIsInviteOpen(false)
        setNewMember({ email: '', role: 'member' })

        toast({
            title: 'Invitation sent',
            description: `An invitation has been sent to ${member.email}`,
        })
    }

    const handleRemove = (id: string) => {
        setMembers(members.filter(m => m.id !== id))
        toast({
            title: 'Member removed',
            description: 'Team member has been removed',
        })
    }

    const getRoleBadge = (role: string) => {
        const colors: Record<string, string> = {
            admin: 'bg-red-100 text-red-800',
            member: 'bg-blue-100 text-blue-800',
            viewer: 'bg-gray-100 text-gray-800',
        }
        return <Badge className={colors[role] || colors.viewer}>{role}</Badge>
    }

    const getStatusBadge = (status: string) => {
        const colors: Record<string, string> = {
            active: 'bg-green-100 text-green-800',
            pending: 'bg-yellow-100 text-yellow-800',
            inactive: 'bg-gray-100 text-gray-800',
        }
        return <Badge className={colors[status] || colors.inactive}>{status}</Badge>
    }

    return (
        <div className="container mx-auto py-8 max-w-5xl">
            <div className="flex justify-between items-center mb-8">
                <div>
                    <h1 className="text-3xl font-bold mb-2">Team Management</h1>
                    <p className="text-muted-foreground">
                        Manage team members and their access levels
                    </p>
                </div>

                <Dialog open={isInviteOpen} onOpenChange={setIsInviteOpen}>
                    <DialogTrigger asChild>
                        <Button>
                            <Plus className="w-4 h-4 mr-2" />
                            Invite Member
                        </Button>
                    </DialogTrigger>
                    <DialogContent>
                        <DialogHeader>
                            <DialogTitle>Invite Team Member</DialogTitle>
                            <DialogDescription>
                                Send an invitation to join your workspace
                            </DialogDescription>
                        </DialogHeader>
                        <div className="space-y-4 py-4">
                            <div className="space-y-2">
                                <Label htmlFor="email">Email Address</Label>
                                <Input
                                    id="email"
                                    type="email"
                                    placeholder="colleague@example.com"
                                    value={newMember.email}
                                    onChange={(e) => setNewMember({ ...newMember, email: e.target.value })}
                                />
                            </div>
                            <div className="space-y-2">
                                <Label>Role</Label>
                                <select
                                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                                    value={newMember.role}
                                    onChange={(e) => setNewMember({ ...newMember, role: e.target.value })}
                                >
                                    <option value="admin">Admin - Full access</option>
                                    <option value="member">Member - Can create and edit</option>
                                    <option value="viewer">Viewer - View only</option>
                                </select>
                            </div>
                        </div>
                        <DialogFooter>
                            <Button variant="outline" onClick={() => setIsInviteOpen(false)}>
                                Cancel
                            </Button>
                            <Button onClick={handleInvite}>
                                <Mail className="w-4 h-4 mr-2" />
                                Send Invitation
                            </Button>
                        </DialogFooter>
                    </DialogContent>
                </Dialog>
            </div>

            <Card>
                <CardHeader>
                    <CardTitle>Team Members ({members.length})</CardTitle>
                    <CardDescription>
                        People who have access to your workspace
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="space-y-4">
                        {members.map((member) => (
                            <div
                                key={member.id}
                                className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50"
                            >
                                <div className="flex items-center gap-4">
                                    <Avatar>
                                        <AvatarImage src={member.avatar} />
                                        <AvatarFallback>
                                            <User className="w-4 h-4" />
                                        </AvatarFallback>
                                    </Avatar>
                                    <div>
                                        <p className="font-medium">{member.name}</p>
                                        <p className="text-sm text-muted-foreground">{member.email}</p>
                                    </div>
                                </div>
                                <div className="flex items-center gap-4">
                                    <div className="flex gap-2">
                                        {getRoleBadge(member.role)}
                                        {getStatusBadge(member.status)}
                                    </div>
                                    <DropdownMenu>
                                        <DropdownMenuTrigger asChild>
                                            <Button variant="ghost" size="sm">
                                                <MoreHorizontal className="w-4 h-4" />
                                            </Button>
                                        </DropdownMenuTrigger>
                                        <DropdownMenuContent align="end">
                                            <DropdownMenuItem>Change Role</DropdownMenuItem>
                                            <DropdownMenuItem>Resend Invite</DropdownMenuItem>
                                            <DropdownMenuItem
                                                className="text-red-600"
                                                onClick={() => handleRemove(member.id)}
                                            >
                                                Remove
                                            </DropdownMenuItem>
                                        </DropdownMenuContent>
                                    </DropdownMenu>
                                </div>
                            </div>
                        ))}
                    </div>
                </CardContent>
            </Card>

            <div className="mt-8 grid grid-cols-3 gap-4">
                <Card>
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium">Total Members</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{members.length}</div>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium">Active</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">
                            {members.filter(m => m.status === 'active').length}
                        </div>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium">Pending</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">
                            {members.filter(m => m.status === 'pending').length}
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    )
}
