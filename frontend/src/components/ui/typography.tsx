import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { Slot } from "@radix-ui/react-slot";
import { cn } from "@/lib/utils";

const typographyVariants = cva("text-foreground", {
  variants: {
    variant: {
      h1: "scroll-m-20 text-3xl font-bold tracking-tight lg:text-4xl",
      h2: "text-2xl font-bold tracking-tight",
      h3: "text-xl font-semibold tracking-tight",
      h4: "text-lg font-semibold tracking-tight",
      p: "leading-7 [&:not(:first-child)]:mt-6",
      lead: "text-xl text-muted-foreground",
      large: "text-lg font-semibold",
      small: "text-sm font-medium leading-none",
      muted: "text-sm text-muted-foreground",
      destructive: "text-sm font-medium text-destructive",
      inlineCode:
        "relative rounded bg-muted px-[0.3rem] py-[0.2rem] font-mono text-sm font-semibold",
      blockquote: "mt-6 border-l-2 border-border pl-6 italic text-muted-foreground",
      list: "my-6 ml-6 list-disc [&>li]:mt-2",
    },
  },
  defaultVariants: {
    variant: "p",
  },
});

type TypographyVariant = NonNullable<
  VariantProps<typeof typographyVariants>["variant"]
>;

const defaultElementMap: Record<TypographyVariant, React.ElementType> = {
  h1: "h1",
  h2: "h2",
  h3: "h3",
  h4: "h4",
  p: "p",
  lead: "p",
  large: "div",
  small: "small",
  muted: "p",
  destructive: "p",
  inlineCode: "code",
  blockquote: "blockquote",
  list: "ul",
};

export interface TypographyProps
  extends React.HTMLAttributes<HTMLElement>,
    VariantProps<typeof typographyVariants> {
  asChild?: boolean;
  as?: React.ElementType;
}

const Typography = React.forwardRef<HTMLElement, TypographyProps>(
  (
    { className, variant = "p", asChild = false, as, children, ...props },
    ref
  ) => {
    const effectiveVariant: TypographyVariant = variant ?? "p";
    const Component = asChild
      ? Slot
      : as || defaultElementMap[effectiveVariant] || "p";

    return (
      <Component
        ref={ref}
        data-slot="typography"
        data-variant={effectiveVariant}
        className={cn(
          typographyVariants({ variant: effectiveVariant, className })
        )}
        {...props}
      >
        {children}
      </Component>
    );
  }
);
Typography.displayName = "Typography";

export { Typography, typographyVariants };
