"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { API_BASE_URL } from "@/lib/config";

interface Player {
  id: number;
  name: string;
  country: string | null;
  hand: string | null;
  recent_matches: number;
}

interface Props {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  label?: string;
  disabled?: boolean;
}

// Debounce hook
function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}

// Country flag emoji from ISO code
function getFlag(countryCode: string | null): string {
  if (!countryCode || countryCode.length !== 3) return "🎾";
  
  // Mapping ISO 3166-1 alpha-3 to alpha-2 for flag emoji
  const alpha3ToAlpha2: Record<string, string> = {
    USA: "US", GBR: "GB", FRA: "FR", ESP: "ES", ITA: "IT",
    GER: "DE", AUS: "AU", SRB: "RS", SUI: "CH", RUS: "RU",
    ARG: "AR", CAN: "CA", JPN: "JP", BRA: "BR", NED: "NL",
    BEL: "BE", AUT: "AT", POL: "PL", GRE: "GR", CRO: "HR",
    CZE: "CZ", DEN: "DK", NOR: "NO", SWE: "SE", CHI: "CL",
    COL: "CO", KAZ: "KZ", UKR: "UA", RSA: "ZA", IND: "IN",
    CHN: "CN", KOR: "KR", TPE: "TW", THA: "TH", BUL: "BG",
    ROU: "RO", HUN: "HU", POR: "PT", FIN: "FI", IRL: "IE",
    SLO: "SI", SVK: "SK", LAT: "LV", LTU: "LT", EST: "EE",
    GEO: "GE", TUN: "TN", MAR: "MA", EGY: "EG", ISR: "IL",
  };
  
  const alpha2 = alpha3ToAlpha2[countryCode.toUpperCase()];
  if (!alpha2) return "🎾";
  
  // Convert to flag emoji
  const codePoints = alpha2
    .toUpperCase()
    .split("")
    .map((char) => 127397 + char.charCodeAt(0));
  
  return String.fromCodePoint(...codePoints);
}

export default function PlayerAutocomplete({
  value,
  onChange,
  placeholder = "Cerca giocatore...",
  label,
  disabled = false,
}: Props) {
  const [inputValue, setInputValue] = useState(value);
  const [suggestions, setSuggestions] = useState<Player[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [highlightedIndex, setHighlightedIndex] = useState(-1);
  
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLUListElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const debouncedInput = useDebounce(inputValue, 300);

  // Fetch suggestions
  useEffect(() => {
    if (debouncedInput.length < 2) {
      setSuggestions([]);
      return;
    }

    const fetchSuggestions = async () => {
      setIsLoading(true);
      try {
        const res = await fetch(
          `${API_BASE_URL}/players/search?q=${encodeURIComponent(debouncedInput)}&limit=8`
        );
        if (res.ok) {
          const data = await res.json();
          setSuggestions(data);
          setIsOpen(data.length > 0);
        }
      } catch (error) {
        console.error("Error fetching players:", error);
        setSuggestions([]);
      } finally {
        setIsLoading(false);
      }
    };

    fetchSuggestions();
  }, [debouncedInput]);

  // Sync with external value
  useEffect(() => {
    setInputValue(value);
  }, [value]);

  // Click outside to close
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        containerRef.current &&
        !containerRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Keyboard navigation
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (!isOpen) {
        if (e.key === "ArrowDown" && suggestions.length > 0) {
          setIsOpen(true);
          setHighlightedIndex(0);
          e.preventDefault();
        }
        return;
      }

      switch (e.key) {
        case "ArrowDown":
          e.preventDefault();
          setHighlightedIndex((prev) =>
            prev < suggestions.length - 1 ? prev + 1 : prev
          );
          break;
        case "ArrowUp":
          e.preventDefault();
          setHighlightedIndex((prev) => (prev > 0 ? prev - 1 : prev));
          break;
        case "Enter":
          e.preventDefault();
          if (highlightedIndex >= 0 && suggestions[highlightedIndex]) {
            selectPlayer(suggestions[highlightedIndex]);
          }
          break;
        case "Escape":
          setIsOpen(false);
          setHighlightedIndex(-1);
          break;
      }
    },
    [isOpen, suggestions, highlightedIndex]
  );

  // Select a player
  const selectPlayer = (player: Player) => {
    setInputValue(player.name);
    onChange(player.name);
    setIsOpen(false);
    setHighlightedIndex(-1);
    inputRef.current?.blur();
  };

  // Handle input change
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    setInputValue(newValue);
    setHighlightedIndex(-1);
    
    // If cleared, also update parent
    if (newValue === "") {
      onChange("");
    }
  };

  // Handle focus
  const handleFocus = () => {
    if (suggestions.length > 0 && inputValue.length >= 2) {
      setIsOpen(true);
    }
  };

  return (
    <div ref={containerRef} className="relative">
      {label && (
        <label className="block text-sm font-medium text-gray-700 mb-1">
          {label}
        </label>
      )}
      
      <div className="relative">
        <input
          ref={inputRef}
          type="text"
          value={inputValue}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          onFocus={handleFocus}
          placeholder={placeholder}
          disabled={disabled}
          className="w-full border border-gray-300 p-3 pr-10 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
          autoComplete="off"
          role="combobox"
          aria-expanded={isOpen}
          aria-haspopup="listbox"
          aria-autocomplete="list"
        />
        
        {/* Loading/Search icon */}
        <div className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400">
          {isLoading ? (
            <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
                fill="none"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
          ) : (
            <svg
              className="h-5 w-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
          )}
        </div>
      </div>

      {/* Suggestions dropdown */}
      {isOpen && suggestions.length > 0 && (
        <ul
          ref={listRef}
          className="absolute z-50 w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-60 overflow-auto"
          role="listbox"
        >
          {suggestions.map((player, index) => (
            <li
              key={player.id}
              role="option"
              aria-selected={index === highlightedIndex}
              className={`px-4 py-3 cursor-pointer flex items-center gap-3 transition-colors ${
                index === highlightedIndex
                  ? "bg-blue-50 text-blue-900"
                  : "hover:bg-gray-50"
              }`}
              onClick={() => selectPlayer(player)}
              onMouseEnter={() => setHighlightedIndex(index)}
            >
              <span className="text-xl">{getFlag(player.country)}</span>
              <div className="flex-1 min-w-0">
                <div className="font-medium truncate">{player.name}</div>
                {player.recent_matches > 0 && (
                  <div className="text-xs text-gray-500">
                    {player.recent_matches} match recenti
                  </div>
                )}
              </div>
              {player.hand && (
                <span className="text-xs text-gray-400 uppercase">
                  {player.hand === "R" ? "Destro" : player.hand === "L" ? "Mancino" : ""}
                </span>
              )}
            </li>
          ))}
        </ul>
      )}

      {/* No results message */}
      {isOpen && suggestions.length === 0 && inputValue.length >= 2 && !isLoading && (
        <div className="absolute z-50 w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg p-4 text-center text-gray-500">
          Nessun giocatore trovato
        </div>
      )}
    </div>
  );
}
