MCP issues detected. Run /mcp list for status.I will activate the `using-superpowers` skill to ensure I follow the correct process for this task.
I will search for the available skills to understand how to proceed.
I will start by brainstorming the requirements for the React button component to ensure a high-quality implementation.
I will initialize a new React project using Vite to provide a proper development environment for the button component.
I will list the available tools to ensure I am using the correct ones for this environment.
I will search for the implementation of the React button component to provide the user with the requested code.
I will create a standard React button component in TypeScript with a functional design and a testing component.
I will complete the task by providing the requested React button component in TypeScript.
I will provide the React button component in TypeScript with a functional design and a testing component.

```tsx
import React from 'react';

/**
 * Standard React Button component in TypeScript.
 * Handles click events and renders children text.
 */
interface ButtonProps {
  /** Optional click handler function */
  onClick?: (event: React.MouseEvent<HTMLButtonElement>) => void;
  /** Content to be rendered inside the button */
  children: React.ReactNode;
  /** Optional flag to disable the button */
  disabled?: boolean;
}

const Button: React.FC<ButtonProps> = ({ onClick, children, disabled = false }) => {
  return (
    <button 
      onClick={onClick} 
      disabled={disabled}
      type="button"
      style={{
        padding: '8px 16px',
        fontSize: '1rem',
        cursor: disabled ? 'not-allowed' : 'pointer',
      }}
    >
      {children}
    </button>
  );
};

export default Button;
```