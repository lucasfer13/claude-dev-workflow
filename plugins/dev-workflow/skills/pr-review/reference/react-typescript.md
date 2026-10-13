# React + TypeScript — review checklist

Rules checkable on a diff; flag only when the diff introduces it (or makes an existing instance worse).

## Hooks and Rules of React

- Hook called inside a condition, loop, nested function, event handler, `try/catch` or after an early `return` — hook order changes between renders, state corrupts or React throws. CRITICAL
- Component function called directly (`Foo()`) instead of rendered as `<Foo />` — hooks attach to the wrong component. IMPORTANT
- Props, state or context value mutated in place (`items.push`, `obj.x = 1`, `state.list.sort()`) — no re-render or stale UI. CRITICAL
- Side effect (fetch, subscription, `localStorage` write, mutation of outer variable, `Math.random()`/`Date.now()` in output) during render — impure render, breaks under Strict Mode. IMPORTANT
- `// eslint-disable` on `react-hooks/exhaustive-deps` or `rules-of-hooks` — hides stale-closure bugs. IMPORTANT
- Component defined inside another component's body — remounts every render, state and focus lost. IMPORTANT

## Effects (You Might Not Need an Effect)

- `useEffect` + `setState` to compute a value from props/state (filtered list, `fullName`, totals) — extra render and flicker; compute during render. IMPORTANT
- `useEffect` that resets or adjusts state when a prop changes where a `key` or storing an ID would do — extra renders, stale intermediate UI. IMPROVEMENT
- Effect used to run logic caused by a user action (submit, click, buy) — belongs in the event handler, can double-fire. IMPORTANT
- Chain of effects that set state to trigger other effects — cascading renders, hard to follow. IMPORTANT
- Fetch in `useEffect` without cleanup/ignore flag or abort — out-of-order responses overwrite newer data (race). IMPORTANT
- Hand-rolled data fetching (`useEffect` + `useState` loading/error/data) in a project that already uses TanStack Query/SWR — no cache, waterfalls, duplicated logic. IMPORTANT
- Manual subscription to an external store (`addEventListener`, `onLine`, `matchMedia`) in an effect with `useState` instead of `useSyncExternalStore` — tearing, leaks. IMPROVEMENT
- Effect that sets up a listener, timer or subscription but returns no cleanup — leak, duplicate handlers after re-run or Strict Mode. IMPORTANT
- Dependency array missing a used value, or object/array/function created in render listed as a dependency — stale closure or effect firing every render. IMPORTANT
- Effect without a dependency array that sets state — infinite render loop. CRITICAL

## State and keys

- State holding a value derivable from other state/props (`fullName`, `isEmpty`, filtered copy) — duplicated truth drifts out of sync. IMPORTANT
- Prop copied into `useState` (`useState(props.x)`) with no `initialX` intent — later prop changes ignored. IMPORTANT
- Several booleans that can contradict (`isLoading` + `isError` + `isSuccess` set manually) instead of one status — impossible UI states. IMPROVEMENT
- Array index as `key` in a list that can reorder, insert or delete, or `key={Math.random()}` / generated during render — remounts, lost input, wrong item state. IMPORTANT
- Missing `key` on elements from `.map()`, or `key` placed on the inner root instead of the component in the array — console warning, wrong reconciliation. IMPORTANT
- Context value created inline (`value={{ a, b }}`) in a frequently re-rendering provider — every consumer re-renders. IMPROVEMENT

## Memoization and performance

- `useMemo`/`useCallback`/`React.memo` added broadly with no measured problem or on cheap values — noise, hides intent, no gain. IMPROVEMENT
- `useCallback` passed to a child that is not memoized (or inline object/array props to a `memo` child) — memoization never hits. IMPROVEMENT
- `memo` with custom `arePropsEqual` that ignores function props or does deep equality — stale closures, slow compare. IMPROVEMENT
- Large list rendered in full with no virtualisation or pagination on unbounded data — slow render and memory. IMPROVEMENT

## TypeScript

- `any` (explicit, implicit via missing types, or `as any`) introduced — disables checking; use `unknown` and narrow. IMPORTANT
- `as SomeType` assertion on data from an API, `JSON.parse` or `catch` instead of validating/narrowing (zod, type guard) — wrong shape fails silently at runtime. IMPORTANT
- `value!` non-null assertion or `as unknown as T` double cast to silence the compiler — runtime null error or lie to the type system. IMPORTANT
- `// @ts-ignore` / `@ts-expect-error` without a reason, or `strict`/`noImplicitAny`/`strictNullChecks` loosened in tsconfig — turns off the safety net. IMPORTANT
- Promise returned and not handled (`no-floating-promises`), or `async` function passed where a void callback is expected (`no-misused-promises`) — unhandled rejection, errors swallowed. IMPORTANT
- `async` function with no `await` — needless promise wrapping. IMPROVEMENT
- Type that duplicates an existing exported type (API model, props of a library component) instead of deriving it (`Pick`, `ComponentProps`, `typeof`) — drifts from source. IMPROVEMENT
- Optional chaining/`?.`/`?? default` on values typed as non-nullable (`no-unnecessary-condition`) — defensive noise that hides the real contract. IMPROVEMENT

## Server state (TanStack Query)

- Query key missing a variable that `queryFn` uses — wrong cache entry served, no refetch on change. IMPORTANT
- `useQuery` data copied into `useState` (or into a form) and then used — loses background updates; derive or use `select`. IMPORTANT
- Mutation that does not invalidate or update the affected query keys — UI shows stale data after write. IMPORTANT
- Dependent query without `enabled` guard (runs with `undefined` id) — bogus request. IMPORTANT
- Default `staleTime` left untouched for data that is static or expensive, or `refetchOnWindowFocus` disabled globally to hide a bug — needless traffic or stale data. IMPROVEMENT
- Errors from query/mutation neither shown nor handled (no `isError`/`onError`/error boundary) — silent failure. IMPORTANT
- Fetch logic and query keys duplicated inline in components instead of one custom hook per query — keys drift between files. IMPROVEMENT

## Accessibility

- `<div>`/`<span>` with `onClick` instead of `<button>`/`<a>`, or `role="button"` without keyboard handling and focus — keyboard and screen-reader users blocked. IMPORTANT
- `<img>` without `alt` (or decorative image without `alt=""`), or alt text like "image of" — missing/noisy description. IMPORTANT
- Form input without an associated `<label>` (`htmlFor`/wrapping) or `aria-label`; placeholder used as the only label — unlabeled control. IMPORTANT
- `<a>` without a real `href` used as a button, or empty/ambiguous link text ("click here") — broken navigation semantics. IMPROVEMENT
- Redundant or invalid ARIA (`role` on an element that already has it, `aria-*` not valid for the role, `<ul role="navigation">`) — worse than no ARIA. IMPROVEMENT
- Positive `tabIndex`, `autoFocus` on non-modal content, or `tabIndex` on non-interactive elements — breaks focus order. IMPROVEMENT
- Error/status message appearing without `role="alert"`/live region, or meaning conveyed by colour only — not announced. IMPROVEMENT

## Over-engineering / AI slop (React)

- Custom hook, context, reducer or store introduced for state used by one component — indirection with no reuse. IMPROVEMENT
- Wrapper component that only forwards props to another component or renders `<div>{children}</div>` — extra layer. IMPROVEMENT
- Util/helper reimplementing what exists in the repo or platform (`lodash`-like, date formatting, `Intl`) — duplication. IMPROVEMENT
- New dependency added for something a few lines or an existing dependency already does — bundle and maintenance cost. IMPROVEMENT
- `try/catch` around code that cannot throw, `if (x)` guards on props that are required by type, redundant `?? []` — defensive noise. IMPROVEMENT
- Comments narrating JSX or restating the code, leftover `console.log`, commented-out code, unused imports/props — clutter. IMPROVEMENT
- `dangerouslySetInnerHTML` with unsanitised data, or tokens/secrets in client code or `localStorage` — XSS, credential exposure. CRITICAL

## Tests

- Snapshot-only or "renders without crashing" test for a component with logic — asserts nothing about behaviour. IMPROVEMENT
- Test queries by CSS class/test internals (`container.querySelector`, state) instead of role/label/text and user events — brittle, ignores accessibility. IMPROVEMENT
- Async UI asserted without `await`/`findBy*`/`waitFor`, or fixed `setTimeout` waits — flaky or false pass. IMPORTANT
- Hook/effect/error-path change (loading, error, empty, race) with no test while only the happy path is covered — regression risk. IMPROVEMENT
- Test deleted, `.skip`/`.only` committed, or assertion loosened alongside a behaviour change — hides a regression. IMPORTANT

## Sources

- https://react.dev/reference/rules/rules-of-hooks
- https://react.dev/reference/rules
- https://react.dev/learn/you-might-not-need-an-effect
- https://react.dev/learn/rendering-lists
- https://react.dev/learn/choosing-the-state-structure
- https://react.dev/reference/react/memo
- https://react.dev/reference/react/useEffect
- https://www.typescriptlang.org/tsconfig/#strict
- https://www.typescriptlang.org/docs/handbook/2/everyday-types.html
- https://typescript-eslint.io/rules/?=recommended-strict
- https://tanstack.com/query/latest/docs/framework/react/guides/important-defaults
- https://tkdodo.eu/blog/practical-react-query
- https://github.com/jsx-eslint/eslint-plugin-jsx-a11y
- https://www.w3.org/WAI/ARIA/apg/practices/read-me-first/
