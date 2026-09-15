import type { ComponentProps } from 'react';

/** Page transitions use the browser so a failed RSC navigation cannot swallow a click. */
export default function ProjectLink({ children, ...props }: ComponentProps<'a'>) {
  return <a {...props}>{children}</a>;
}
