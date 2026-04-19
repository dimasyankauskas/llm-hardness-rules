```tsx
// Button.tsx
import { ButtonHTMLAttributes, ReactNode } from "react";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode;
  onClick: () => void;
}

export function Button({ children, onClick, ...rest }: ButtonProps) {
  return (
    <button onClick={onClick} {...rest}>
      {children}
    </button>
  );
}
```

**Usage:**

```tsx
<Button onClick={() => console.log("clicked")}>Click me</Button>
```

Extends native `HTMLButtonElement` attrs so `disabled`, `type`, `className`, etc. work without extra props.