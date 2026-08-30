import { createContext, useContext, useState, type ReactNode } from 'react'

const ROLE_KEY = 'clarity_role'

interface RoleContextValue {
  role: string
  setRole: (role: string) => void
}

const RoleContext = createContext<RoleContextValue>({ role: 'global_exec', setRole: () => {} })

function readStoredRole(): string {
  try {
    return localStorage.getItem(ROLE_KEY) || 'global_exec'
  } catch {
    return 'global_exec'
  }
}

export function RoleProvider({ children }: { children: ReactNode }) {
  const [role, setRoleState] = useState<string>(readStoredRole)

  const setRole = (r: string) => {
    setRoleState(r)
    try {
      localStorage.setItem(ROLE_KEY, r)
    } catch {
      /* per-viewer convenience only — safe to ignore if storage is unavailable */
    }
  }

  return <RoleContext.Provider value={{ role, setRole }}>{children}</RoleContext.Provider>
}

export function useRole() {
  return useContext(RoleContext)
}
