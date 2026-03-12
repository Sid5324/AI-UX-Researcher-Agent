'use client'

import { useEffect, useState, useCallback } from 'react'
import { subscribeToConnection, getConnectionState, checkBackendHealth } from '@/lib/api'

export function useConnection() {
    const [isOnline, setIsOnline] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [checking, setChecking] = useState(false)

    useEffect(() => {
        // Get initial state
        const state = getConnectionState()
        setIsOnline(state.isOnline)
        setError(state.lastError)

        // Subscribe to changes
        const unsubscribe = subscribeToConnection((online, err) => {
            setIsOnline(online)
            setError(err)
        })

        return () => { unsubscribe() }
    }, [])

    const checkConnection = useCallback(async () => {
        setChecking(true)
        try {
            const healthy = await checkBackendHealth()
            setIsOnline(healthy)
            if (!healthy) {
                setError('Backend server is offline')
            } else {
                setError(null)
            }
            return healthy
        } finally {
            setChecking(false)
        }
    }, [])

    return {
        isOnline,
        error,
        checking,
        checkConnection,
    }
}
