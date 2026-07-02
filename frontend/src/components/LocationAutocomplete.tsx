import { useEffect, useRef, useState } from 'react'
import { searchLocations } from '../api/client'
import type { LocationSuggestion } from '../types/trip'

const DEBOUNCE_MS = 300
const MIN_QUERY_LENGTH = 3

export default function LocationAutocomplete({
  label,
  value,
  onChange,
  placeholder,
  error,
}: {
  label: string
  value: string
  onChange: (value: string) => void
  placeholder?: string
  error?: string
}) {
  const [suggestions, setSuggestions] = useState<LocationSuggestion[]>([])
  const [isOpen, setIsOpen] = useState(false)
  const [highlightedIndex, setHighlightedIndex] = useState(-1)
  const debounceRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined)
  const abortRef = useRef<AbortController | undefined>(undefined)
  const containerRef = useRef<HTMLDivElement>(null)

  function closeAndCancelPending() {
    if (debounceRef.current) clearTimeout(debounceRef.current)
    abortRef.current?.abort()
    setIsOpen(false)
  }

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        closeAndCancelPending()
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
      if (debounceRef.current) clearTimeout(debounceRef.current)
      abortRef.current?.abort()
    }
  }, [])

  function handleInputChange(next: string) {
    onChange(next)
    setHighlightedIndex(-1)

    if (debounceRef.current) clearTimeout(debounceRef.current)
    abortRef.current?.abort()

    if (next.trim().length < MIN_QUERY_LENGTH) {
      setSuggestions([])
      setIsOpen(false)
      return
    }

    debounceRef.current = setTimeout(async () => {
      const controller = new AbortController()
      abortRef.current = controller
      try {
        const results = await searchLocations(next.trim(), controller.signal)
        setSuggestions(results)
        setIsOpen(results.length > 0)
      } catch {
        // Stale/aborted requests or a flaky lookup shouldn't disrupt typing --
        // the user can still submit the free-typed value as-is.
      }
    }, DEBOUNCE_MS)
  }

  function selectSuggestion(suggestion: LocationSuggestion) {
    onChange(suggestion.display_name)
    setSuggestions([])
    setHighlightedIndex(-1)
    closeAndCancelPending()
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (!isOpen || suggestions.length === 0) return
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setHighlightedIndex((i) => (i + 1) % suggestions.length)
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setHighlightedIndex((i) => (i <= 0 ? suggestions.length - 1 : i - 1))
    } else if (e.key === 'Enter' && highlightedIndex >= 0) {
      e.preventDefault()
      selectSuggestion(suggestions[highlightedIndex])
    } else if (e.key === 'Escape') {
      closeAndCancelPending()
    }
  }

  return (
    <div ref={containerRef} className="relative">
      <label className="block text-sm">
        <span className="mb-1 block font-medium text-gray-700">{label}</span>
        <input
          type="text"
          value={value}
          onChange={(e) => handleInputChange(e.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={() => suggestions.length > 0 && setIsOpen(true)}
          placeholder={placeholder}
          autoComplete="off"
          role="combobox"
          aria-expanded={isOpen}
          aria-autocomplete="list"
          className={`w-full rounded-md border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 ${
            error ? 'border-red-400' : 'border-gray-300'
          }`}
        />
        {error && <span className="mt-1 block text-xs text-red-600">{error}</span>}
      </label>

      {isOpen && (
        <ul className="absolute z-10 mt-1 max-h-56 w-full overflow-auto rounded-md border border-gray-200 bg-white text-sm shadow-lg">
          {suggestions.map((s, i) => (
            <li key={`${s.display_name}-${i}`}>
              <button
                type="button"
                onMouseDown={(e) => e.preventDefault()}
                onClick={() => selectSuggestion(s)}
                className={`block w-full px-3 py-2 text-left hover:bg-brand-50 ${
                  i === highlightedIndex ? 'bg-brand-50' : ''
                }`}
              >
                {s.display_name}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
