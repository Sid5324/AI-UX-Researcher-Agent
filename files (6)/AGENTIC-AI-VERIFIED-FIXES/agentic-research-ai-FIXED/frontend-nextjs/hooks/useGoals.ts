'use client'

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { goalsApi } from '@/lib/api'

export function useGoals() {
  return useQuery({
    queryKey: ['goals'],
    queryFn: goalsApi.listGoals,
    refetchInterval: 5000,
  })
}

export function useGoal(goalId: string) {
  return useQuery({
    queryKey: ['goal', goalId],
    queryFn: () => goalsApi.getGoal(goalId),
    enabled: Boolean(goalId),
    refetchInterval: 4000,
  })
}

export function useCreateGoal() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: goalsApi.createGoal,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['goals'] })
    },
  })
}
