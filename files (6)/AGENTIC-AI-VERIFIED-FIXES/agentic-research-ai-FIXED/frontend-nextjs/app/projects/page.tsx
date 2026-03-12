'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Plus, Search, Folder, Clock, CheckCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { useToast } from '@/components/ui/use-toast'
import { goalsApi } from '@/lib/api'

interface Project {
    id: string
    name: string
    description: string
    status: 'active' | 'completed' | 'archived'
    goals_count: number
    created_at: string
}

export default function ProjectsPage() {
    const router = useRouter()
    const { toast } = useToast()
    const [projects, setProjects] = useState<Project[]>([])
    const [loading, setLoading] = useState(true)
    const [searchQuery, setSearchQuery] = useState('')
    const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false)
    const [newProject, setNewProject] = useState({ name: '', description: '' })

    useEffect(() => {
        loadProjects()
    }, [])

    const loadProjects = async () => {
        try {
            setLoading(true)
            const goals = await goalsApi.listGoals()

            const projectMap = new Map<string, Project>()

            goals.forEach((goal) => {
                const projectId = 'default'
                const projectName = 'My Research Projects'

                if (!projectMap.has(projectId)) {
                    projectMap.set(projectId, {
                        id: projectId,
                        name: projectName,
                        description: `Research goals collection`,
                        status: 'active',
                        goals_count: 0,
                        created_at: goal.created_at
                    })
                }

                const project = projectMap.get(projectId)!
                project.goals_count++
            })

            setProjects(Array.from(projectMap.values()))
        } catch (error) {
            console.error('Failed to load projects:', error)
            toast({
                title: 'Error',
                description: 'Failed to load projects',
                variant: 'destructive'
            })
        } finally {
            setLoading(false)
        }
    }

    const handleCreateProject = async () => {
        if (!newProject.name.trim()) {
            toast({
                title: 'Validation Error',
                description: 'Project name is required',
                variant: 'destructive'
            })
            return
        }

        try {
            const newProjectData: Project = {
                id: `project-${Date.now()}`,
                name: newProject.name,
                description: newProject.description,
                status: 'active',
                goals_count: 0,
                created_at: new Date().toISOString()
            }

            setProjects([newProjectData, ...projects])
            setIsCreateDialogOpen(false)
            setNewProject({ name: '', description: '' })

            toast({ title: 'Success', description: 'Project created successfully' })
        } catch (error) {
            toast({
                title: 'Error',
                description: 'Failed to create project',
                variant: 'destructive'
            })
        }
    }

    const filteredProjects = projects.filter(project =>
        project.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        project.description.toLowerCase().includes(searchQuery.toLowerCase())
    )

    const getStatusIcon = (status: string) => {
        switch (status) {
            case 'active':
                return <Clock className="h-4 w-4" />
            case 'completed':
                return <CheckCircle className="h-4 w-4" />
            default:
                return <Clock className="h-4 w-4" />
        }
    }

    return (
        <div className="container mx-auto p-8 max-w-7xl">
            {/* Header */}
            <div className="flex items-center justify-between mb-8">
                <div>
                    <h1 className="text-3xl font-bold mb-2">Projects</h1>
                    <p className="text-muted-foreground">
                        Organize your research goals into projects
                    </p>
                </div>

                <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
                    <DialogTrigger asChild>
                        <Button size="lg" className="gap-2">
                            <Plus className="h-5 w-5" />
                            New Project
                        </Button>
                    </DialogTrigger>
                    <DialogContent>
                        <DialogHeader>
                            <DialogTitle>Create New Project</DialogTitle>
                            <DialogDescription>
                                Create a project to organize related research goals
                            </DialogDescription>
                        </DialogHeader>
                        <div className="space-y-4 py-4">
                            <div className="space-y-2">
                                <Label htmlFor="project-name">Project Name</Label>
                                <Input
                                    id="project-name"
                                    placeholder="e.g., Mobile App Research"
                                    value={newProject.name}
                                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setNewProject({ ...newProject, name: e.target.value })}
                                />
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="project-description">Description</Label>
                                <Textarea
                                    id="project-description"
                                    placeholder="What is this project about?"
                                    rows={3}
                                    value={newProject.description}
                                    onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setNewProject({ ...newProject, description: e.target.value })}
                                />
                            </div>
                        </div>
                        <DialogFooter>
                            <Button variant="outline" onClick={() => setIsCreateDialogOpen(false)}>
                                Cancel
                            </Button>
                            <Button onClick={handleCreateProject}>Create Project</Button>
                        </DialogFooter>
                    </DialogContent>
                </Dialog>
            </div>

            {/* Search */}
            <div className="flex gap-4 mb-6">
                <div className="flex-1 relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                        placeholder="Search projects..."
                        className="pl-10"
                        value={searchQuery}
                        onChange={(e: React.ChangeEvent<HTMLInputElement>) => setSearchQuery(e.target.value)}
                    />
                </div>
            </div>

            {/* Projects Grid */}
            {loading ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {[1, 2, 3].map((i) => (
                        <Card key={i} className="animate-pulse">
                            <CardHeader>
                                <div className="h-6 bg-muted rounded w-3/4 mb-2" />
                                <div className="h-4 bg-muted rounded w-full" />
                            </CardHeader>
                        </Card>
                    ))}
                </div>
            ) : filteredProjects.length === 0 ? (
                <div className="text-center py-12">
                    <Folder className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
                    <h3 className="text-xl font-semibold mb-2">No projects found</h3>
                    <Button onClick={() => setIsCreateDialogOpen(true)} className="gap-2">
                        <Plus className="h-4 w-4" />
                        Create Project
                    </Button>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {filteredProjects.map((project) => (
                        <Card
                            key={project.id}
                            className="hover:shadow-lg transition-shadow cursor-pointer"
                            onClick={() => router.push(`/projects/${project.id}`)}
                        >
                            <CardHeader>
                                <div className="flex items-start justify-between">
                                    <div className="flex-1">
                                        <CardTitle className="mb-2 flex items-center gap-2">
                                            <Folder className="h-5 w-5 text-primary" />
                                            {project.name}
                                        </CardTitle>
                                        <CardDescription className="line-clamp-2">
                                            {project.description || 'No description'}
                                        </CardDescription>
                                    </div>
                                    <Badge variant="secondary" className="gap-1">
                                        {getStatusIcon(project.status)}
                                        {project.status}
                                    </Badge>
                                </div>
                            </CardHeader>
                            <CardContent>
                                <div className="space-y-2">
                                    <div className="flex items-center justify-between text-sm">
                                        <span className="text-muted-foreground">Goals</span>
                                        <span className="font-medium">{project.goals_count}</span>
                                    </div>
                                    <div className="flex items-center justify-between text-sm">
                                        <span className="text-muted-foreground">Created</span>
                                        <span className="font-medium">
                                            {new Date(project.created_at).toLocaleDateString()}
                                        </span>
                                    </div>
                                </div>
                            </CardContent>
                            <CardFooter>
                                <Button variant="ghost" className="w-full">
                                    View Details
                                </Button>
                            </CardFooter>
                        </Card>
                    ))}
                </div>
            )}
        </div>
    )
}
