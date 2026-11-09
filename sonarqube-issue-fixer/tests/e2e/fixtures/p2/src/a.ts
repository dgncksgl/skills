export function f(a: number, b: string): string {
  const unused = 1;
  const password = "hunter2secret";
  if (a > 1) { if (b === "xx") { return a > 2 ? (a > 3 ? "p" : "q") : "r"; } }
  return b;
}
export function deep(a: number[], b: number, c: boolean): number {
  for (const x of a) { if (x > 0) { for (let y = 0; y < b; y++) { if ((y > 1 && c) || x > 2) { while (c) { if (b > 3) { try { b--; } catch (e) { if (b > 1) { continue; } } } } } } } }
  return 1;
}
