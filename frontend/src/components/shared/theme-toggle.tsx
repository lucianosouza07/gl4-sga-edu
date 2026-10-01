import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Tooltip, TooltipTrigger, TooltipContent } from "@/components/ui/tooltip";
import { Moon, Sun } from "lucide-react";

export function ThemeToggle() {
  const [isDark, setIsDark] = useState<boolean>(() => {
    if (typeof window !== "undefined") {
      const saved = localStorage.getItem("theme");
      if (saved) return saved === "dark";
      return window.matchMedia("(prefers-color-scheme: dark)").matches;
    }
    return false;
  });

  useEffect(() => {
    const root = document.documentElement;
    if (isDark) {
      root.classList.add("dark");
      localStorage.setItem("theme", "dark");
    } else {
      root.classList.remove("dark");
      localStorage.setItem("theme", "light");
    }
  }, [isDark]);

  return (
    <Tooltip>
      <TooltipTrigger
        render={
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setIsDark(!isDark)}
            className="size-9 rounded-md text-muted-foreground hover:text-foreground hover:bg-accent"
            aria-label="Alternar tema claro/escuro"
          >
            {isDark ? (
              <Sun className="size-4 text-amber-400 transition-transform hover:rotate-45" />
            ) : (
              <Moon className="size-4 text-foreground/80 transition-transform hover:-rotate-12" />
            )}
          </Button>
        }
      />
      <TooltipContent side="bottom">
        {isDark ? "Mudar para modo claro" : "Mudar para modo escuro"}
      </TooltipContent>
    </Tooltip>
  );
}
