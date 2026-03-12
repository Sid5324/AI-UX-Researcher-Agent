"use client"

import { useToast } from "@/components/ui/use-toast"
import { cn } from "@/lib/utils"
import { X } from "lucide-react"
import * as React from "react"

export function Toaster() {
  const { toasts } = useToast()

  return (
    <div className="fixed bottom-0 right-0 z-50 flex flex-col gap-2 p-4">
      {toasts.map(function ({ id, title, description, action, variant, ...props }) {
        return (
          <div
            key={id}
            className={cn(
              "group relative pointer-events-auto flex w-full items-center justify-between space-x-4 overflow-hidden rounded-md border p-6 pr-8 shadow-lg transition-all",
              variant === "destructive"
                ? "border-destructive/50 bg-destructive text-destructive-foreground"
                : "bg-background text-foreground"
            )}
            {...props}
          >
            <div className="flex flex-col gap-1">
              {title && <div className="text-sm font-semibold">{title}</div>}
              {description && (
                <div className={cn("text-sm", variant === "destructive" ? "opacity-90" : "opacity-90")}>
                  {description}
                </div>
              )}
            </div>
            {action && (
              <button
                onClick={action.props.onClick}
                className="inline-flex h-8 shrink-0 items-center justify-center rounded-md border bg-transparent px-3 text-sm font-medium hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-slate-400 focus:ring-offset-2 disabled:pointer-events-none disabled:opacity-50"
              >
                {action.props.children}
              </button>
            )}
            <button
              onClick={() => {
                const event = new CustomEvent("toast-dismiss", { detail: id })
                window.dispatchEvent(event)
              }}
              className="absolute right-2 top-2 rounded-md p-1 text-foreground/50 opacity-0 transition-opacity hover:text-foreground focus:opacity-100 focus:outline-none focus:ring-2 group-hover:opacity-100"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        )
      })}
    </div>
  )
}
