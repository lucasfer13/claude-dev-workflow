# Android / Kotlin — review checklist

Rules checkable on a diff; flag only when the diff introduces it (or makes an existing instance worse).

## Coroutines

- `GlobalScope.launch/async` — not cancelled with any lifecycle, leaks, untestable; inject a scope or use `viewModelScope`/`lifecycleScope`. IMPORTANT
- Hardcoded `Dispatchers.IO/Default` in `withContext` or `launch` inside a class — tests cannot swap it; inject a dispatcher. IMPROVEMENT
- Blocking call (`Thread.sleep`, `runBlocking`, blocking IO/DB/network) in a suspend function or on the main thread without `withContext` — ANR or frozen UI. CRITICAL
- `runBlocking` in production code outside `main`/tests — blocks the calling thread, deadlock risk. IMPORTANT
- `catch (e: Exception)` / `Throwable` in a coroutine that swallows `CancellationException` — breaks cancellation, coroutine keeps running. IMPORTANT
- `try/catch` around `launch { }` or `async { }` call expecting to catch the child's exception — never fires; exception propagates to the scope. IMPORTANT
- `async { }.await()` immediately, or `launch` + `join` right after — pointless concurrency; call the suspend function directly. IMPROVEMENT
- `suspend` function that does no suspending work, or `withContext(Dispatchers.Main)` around code already on main — misleading signature, noise. IMPROVEMENT
- Long loop in a coroutine with no `ensureActive()`/suspension point — cancellation ignored. IMPROVEMENT
- `viewModelScope.launch` started inside a composable or Activity to do UI animation (`drawerState.close()`) — IllegalStateException; use a composition scope. IMPORTANT

## Flow and lifecycle

- `flow.collect` in `lifecycleScope.launch` directly in an Activity/Fragment (no `repeatOnLifecycle(STARTED)`) — collects in background, wasted work or crash. IMPORTANT
- `collectAsState()` instead of `collectAsStateWithLifecycle()` in an Android Compose screen — upstream keeps running when the UI is not visible. IMPORTANT
- `MutableStateFlow`/`MutableLiveData` exposed publicly from a ViewModel instead of read-only `StateFlow` via `asStateFlow()` — any caller can change state. IMPORTANT
- Several separate state flows/fields for one screen where a single `uiState` object fits — inconsistent intermediate UI. IMPROVEMENT
- `stateIn`/`shareIn` with `SharingStarted.Eagerly` for UI state, or `WhileSubscribed` omitted — upstream runs forever. IMPROVEMENT
- One-off event (navigation, toast) modelled as state that is re-delivered after rotation, or sent through a `Channel`/`SharedFlow` from the ViewModel and dropped — duplicated or lost events. IMPORTANT

## Architecture, ViewModel and DI

- ViewModel holds `Context`, `Activity`, `View`, `Resources` or a composable reference — memory leak; `AndroidViewModel` added without need. IMPORTANT
- ViewModel instance passed to child composables or helper classes instead of state + lambdas — couples UI to ViewModel. IMPROVEMENT
- Business logic or data access in an Activity/Fragment/composable instead of the ViewModel/data layer — untestable, lost on recreation. IMPORTANT
- UI layer touching Retrofit/Room/DAO directly instead of a repository — layers bypassed. IMPROVEMENT
- Repository/UseCase/Mapper/Manager class that only forwards to one call, or interface with one implementation and no second use — ceremony. IMPROVEMENT
- Hilt: `@Singleton` on stateless classes or on something holding Activity-scoped data — memory held for app lifetime. IMPROVEMENT
- Hilt: field injection or manual `Foo()` construction where constructor injection works; private `@Inject` field — compile error or hidden dependency. IMPROVEMENT
- `@Binds`/`@Provides` added for a class that already has an `@Inject` constructor and no interface need — redundant module code. IMPROVEMENT
- Singletons/`object` holding mutable app state or a `Context` (static references) instead of DI — leaks, test coupling. IMPORTANT
- Mocks everywhere in new tests where a simple fake of the repository would do — brittle, tests implementation. IMPROVEMENT

## Compose

- Mutable collection (`mutableListOf`, `ArrayList`) held as Compose state or mutated in place — no recomposition, stale UI. IMPORTANT
- Expensive computation (sort/filter/map of a large list) in a composable body without `remember(keys)` or moved to the ViewModel — runs every recomposition. IMPROVEMENT
- `LazyColumn`/`LazyRow` `items(...)` without a stable `key` — state mixed up on reorder, extra recomposition. IMPROVEMENT
- State written during composition (backwards write) instead of in an event/effect — endless recomposition. CRITICAL
- Frequently changing state read high in the tree (scroll offset, animation) and passed as a value instead of a lambda/`Modifier.offset { }`/`drawBehind` — recomposes the whole subtree. IMPROVEMENT
- `derivedStateOf` missing for a threshold derived from fast-changing state (`firstVisibleItemIndex > 0`), or used where a plain value is enough — extra recompositions or needless complexity. IMPROVEMENT
- `remember { }` for state that must survive rotation/process death (input text, selection) — lost on recreation; use `rememberSaveable`. IMPORTANT
- State hoisted far above where it is used, or whole `UiState` passed to leaf composables that need one field — unneeded recomposition and coupling. IMPROVEMENT
- Side effect in composition body (network call, `launch`, analytics) instead of `LaunchedEffect`/`DisposableEffect`; `LaunchedEffect(Unit)` capturing changing values without keys — repeated or stale work. IMPORTANT

## Kotlin language and idioms

- `!!` on a nullable that the code does not prove non-null (platform types, map lookups, `findViewById`) — NPE at runtime; use `?.`, `?:`, `requireNotNull`, `checkNotNull`. IMPORTANT
- `lateinit var` for something that could be a constructor parameter or `by lazy`, or accessed before init — `UninitializedPropertyAccessException`. IMPROVEMENT
- `var` or mutable collection (`MutableList`, `ArrayList`) where `val`/read-only `List` is enough, or exposed publicly — unneeded mutability. IMPROVEMENT
- Java-style null check `if (x != null) { x.foo() }` on a `var` property, or `x?.let { }` used for a plain statement/non-null value — noise or smart-cast failure. IMPROVEMENT
- `if/else` or `when` chain assigning a variable where an expression body/`when` expression returns the value — verbose. IMPROVEMENT
- `when` on a sealed type/enum with an `else` branch — new subtype silently handled wrongly; drop `else`. IMPORTANT
- Overloads instead of default parameters, or multiple same-typed/Boolean params at call sites without named arguments — swapped-argument bugs. IMPROVEMENT
- `object`/class named `Util`, `Helper`, `Manager`, or Java-style getters/setters (`getX()`) instead of properties/extensions — non-idiomatic. IMPROVEMENT
- Hardcoded user-facing strings, colours or dimensions instead of resources — localisation and theming break. IMPROVEMENT
- Catch-all `catch (e: Exception) { }` or `e.printStackTrace()` instead of logging/handling a specific type — errors swallowed. IMPORTANT
- Unused imports/parameters/private functions, commented-out code, KDoc restating the name — clutter. IMPROVEMENT

## Room, networking, persistence

- Room DAO query returning a large unbounded list synchronously (`fun getAll(): List<T>` called on main) instead of `suspend`/`Flow` — main-thread DB access, crash. CRITICAL
- `@Entity`/schema changed with no migration (`fallbackToDestructiveMigration()` added) or `version` not bumped — user data loss or crash on update. CRITICAL
- Multiple related writes without `@Transaction` — partial state on failure. IMPORTANT
- Room database or Retrofit/OkHttp client constructed per call instead of once via DI — expensive, leaks. IMPORTANT
- Network/DB errors not mapped to UI state (loading/error/empty), exceptions bubbling into `viewModelScope` uncaught — crash or blank screen. IMPORTANT
- Secrets, tokens or API keys hardcoded in source/`BuildConfig` committed, or sensitive data in logs/`SharedPreferences` plaintext — credential leak. CRITICAL
- Permission, exported component or `WebView` setting (`setJavaScriptEnabled`, `allowFileAccess`) added without need — attack surface. IMPORTANT

## Java (when the diff touches .java)

- `equals` overridden without `hashCode` (or vice versa), or `equals` not symmetric/consistent — broken in `HashMap`/`HashSet`. IMPORTANT
- Mutable object exposed or stored directly (getter returning internal `List`/`Date`/array, constructor keeping the caller's reference) — callers alter internal state; copy or make immutable. IMPORTANT
- `Optional` used as a field, method parameter or collection element, or `Optional.get()` without `isPresent` — misuse, NoSuchElementException. IMPROVEMENT
- Catching `Exception`/`Throwable`, empty `catch`, or swallowing `InterruptedException` without restoring the flag — failures hidden. IMPORTANT
- Resource (stream, cursor, connection) not closed with try-with-resources — leak. IMPORTANT
- Returning `null` for an empty collection/array instead of an empty one — NPEs at every caller. IMPROVEMENT
- Raw types or unchecked casts added without justification — ClassCastException at runtime. IMPROVEMENT

## Sources

- https://kotlinlang.org/docs/coding-conventions.html
- https://kotlinlang.org/docs/idioms.html
- https://developer.android.com/topic/architecture/recommendations
- https://developer.android.com/kotlin/coroutines/coroutines-best-practices
- https://developer.android.com/topic/libraries/architecture/coroutines
- https://developer.android.com/develop/ui/compose/performance/bestpractices
- https://developer.android.com/develop/ui/compose/state-hoisting
- https://developer.android.com/develop/ui/compose/state
- https://developer.android.com/training/data-storage/room
- https://developer.android.com/training/dependency-injection/hilt-android
- https://developer.android.com/topic/libraries/architecture/viewmodel
