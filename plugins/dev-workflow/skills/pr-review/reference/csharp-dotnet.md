# C# / .NET — review checklist

Rules checkable on a diff; flag only when the diff introduces it (or makes an existing instance worse).

## Async and threading

- `.Result` / `.Wait()` / `.GetAwaiter().GetResult()` on a Task in a request path or hosted service — thread-pool starvation, deadlock. IMPORTANT
- `async void` method that is not an event handler — exceptions are unobservable and can crash the process; after an ASP.NET request completes it writes to a recycled context. CRITICAL
- `Task.Run(...)` wrapped around async or sync work and then awaited inside a request — extra scheduling, no scalability gain. IMPORTANT
- `async` method with no `await` (or `async`/`await` around a single pass-through return in a trivial method) — useless state machine, hides intent. IMPROVEMENT
- `CancellationToken` accepted but not passed to the inner awaited call (EF, HttpClient, streams), or controller action without a token on a long call — work continues after client disconnect. IMPROVEMENT
- Fire-and-forget `_ = SomethingAsync()` or `Task.Run` in a controller capturing `HttpContext`, a scoped service or `DbContext` — ObjectDisposedException or wrong-request data. CRITICAL
- Synchronous I/O in an async path (`File.ReadAllText`, `StreamReader.ReadToEnd`, `Request.Form`, sync `SaveChanges`) — blocks a pool thread. IMPORTANT
- `Task.WhenAll` over tasks that share one `DbContext` or `HttpContext` — not thread-safe, random failures. CRITICAL
- Mutable static field or singleton state written from request code without synchronisation — data races between requests. CRITICAL
- Async work in a constructor or DI factory (`.Result` inside `AddSingleton(sp => ...)`) — deadlock at resolve; use `CreateAsync` or hosted init. IMPORTANT

## Dependency injection and lifetimes

- Singleton (or `static`) holding a scoped service or `DbContext` via constructor — captive dependency, stale or disposed instance. CRITICAL
- `IServiceProvider.GetService/GetRequiredService` inside business code (service locator) when constructor injection works — hidden dependencies, untestable. IMPORTANT
- `AddTransient` for an `IDisposable` resolved from the root scope — container keeps it alive until shutdown, memory leak. IMPORTANT
- New interface with exactly one implementation and one consumer, plus its `AddScoped` line, with no test double or second implementation planned — ceremony without benefit. IMPROVEMENT
- Service/Manager/Helper/Wrapper class that only forwards to another service or `DbContext` method — extra layer with no behaviour. IMPROVEMENT
- `new` of a collaborator (client, repository, service) inside a class instead of injecting it — couples to implementation, blocks testing. IMPORTANT
- Configuration read via `IConfiguration["Key"]` scattered in code instead of validated options (`IOptions<T>` with `ValidateOnStart`) — typos fail silently at runtime. IMPROVEMENT

## Data access (EF Core / SQL)

- Query inside a `foreach`/LINQ projection that triggers one query per item (N+1), or lazy-loading proxies enabled — latency grows with row count. IMPORTANT
- Loading whole entities to use one or two columns instead of `.Select(...)` — over-fetching. IMPROVEMENT
- Collection endpoint without `Take`/paging (`ToListAsync()` on an unbounded table) — OOM and slow response at real data volumes. IMPORTANT
- `ToList()` / `ToArray()` followed by `.Where` / `.Count()` / `.Any()` in memory — filter happens client-side after full load. IMPORTANT
- String-built SQL (`FromSqlRaw($"...{x}")`, `ExecuteSqlRaw` with interpolation, Dapper with concatenation) — SQL injection. CRITICAL
- `DbContext` stored in a singleton/static or shared across threads — not thread-safe, stale tracking. CRITICAL
- Schema/entity change without a matching migration, or migration that drops/renames data without a backfill — deploy-time data loss. CRITICAL

## Errors and exceptions

- `catch (Exception)` / bare `catch` that logs and continues or returns a default — hides real failures, partial state. IMPORTANT
- Empty `catch` block, or `catch` that only does `return null`/`false` — failure silently lost. CRITICAL
- `throw ex;` instead of `throw;` — destroys the original stack trace. IMPORTANT
- New exception thrown without the inner exception (`throw new X(msg)` inside a `catch`) — root cause lost. IMPORTANT
- Exceptions used for normal control flow (parse/lookup failure caught to branch) where `TryParse`/`TryGetValue`/validation exists — slow and noisy. IMPROVEMENT
- Error response that returns `ex.Message` or stack trace to the client — information disclosure. IMPORTANT

## Nullable reference types and typing

- `!` (null-forgiving) added to silence a warning instead of fixing the flow — NullReferenceException at runtime. IMPORTANT
- `#nullable disable` or `<Nullable>` removed/downgraded, or mass `#pragma warning disable CS86xx` — turns off the safety net. IMPORTANT
- `dynamic`, `object` or `Dictionary<string, object>` used as a data contract where a typed record fits — loses compile-time checks. IMPROVEMENT

## HttpClient and external calls

- `new HttpClient()` per call or `using var client = new HttpClient()` in a request path — socket exhaustion. CRITICAL
- External call with no timeout, no cancellation token and no failure handling — one slow dependency stalls the request. IMPORTANT
- Secrets, API keys or tokens hardcoded or logged — credential leak. CRITICAL

## Logging

- String interpolation or concatenation in a log call (`LogInformation($"...{x}")`) — breaks structured logging and allocates even when the level is off. IMPROVEMENT
- `LogError(ex.Message)` instead of passing the exception object — stack trace lost. IMPORTANT
- Logging whole request/response bodies, tokens, passwords or personal data — privacy and secret leak. CRITICAL

## API and design

- Controller action doing business logic, data access and mapping inline instead of delegating — untestable, bloated action. IMPROVEMENT
- Entity (EF model) returned directly from an API endpoint or accepted as request body — over-posting and leaks internal fields. IMPORTANT
- Public API contract change (route, status code, field rename/removal, enum value) with no versioning or note — breaks existing clients. IMPORTANT
- Missing `[Authorize]`/policy on a new endpoint or an `[AllowAnonymous]` added casually — unauthenticated access. CRITICAL
- `IDisposable`/`IAsyncDisposable` created without `using`/`await using` — handle and connection leak. IMPORTANT

## Over-engineering / AI slop (C#)

- Repository/Unit-of-Work/Mediator/Factory/Strategy layer added on top of EF Core or a simple call with a single use — duplicates what `DbContext` already is. IMPROVEMENT
- Generic `BaseService<T>`, `IGenericRepository<T>` or abstract base introduced for two callers — premature abstraction. IMPROVEMENT
- Helper/Util/Extension method duplicating an existing BCL or project method (`string.IsNullOrWhiteSpace`, `Enumerable` ops, existing mapper) — reinvented wheel. IMPROVEMENT
- Dead code, unused `using`s/parameters/private methods, commented-out blocks left in the diff — clutter. IMPROVEMENT
- `try/catch` wrapped around code that cannot throw, or null/empty checks on values produced by the same method — defensive noise. IMPROVEMENT

## Edge cases specific to .NET

- Culture-sensitive parse/format (`double.Parse`, `ToString("N2")`, string compare/`ToUpper`) without `CultureInfo.InvariantCulture`/`StringComparison` — wrong results on another locale. IMPORTANT
- `FirstOrDefault()`/`Single()` result used without handling empty or multiple — NullReferenceException or InvalidOperationException. IMPORTANT
- `DateTime` compared/stored across time zones without `Kind`/`DateTimeOffset` — off-by-hours bugs. IMPORTANT
- Regex built from user input or run without a timeout — ReDoS. IMPORTANT

## Tests

- New test that asserts nothing meaningful (only "does not throw", only a mock was called) — passes while behaviour is broken. IMPORTANT
- Test that re-implements the production logic to compute the expected value — circular, cannot fail. IMPORTANT
- Mocks/fakes of everything including the class under test's own collaborators and the data layer, no real path exercised — proves wiring only. IMPROVEMENT
- Test with `Thread.Sleep`, real clock, real network or ordering dependency on other tests — flaky. IMPORTANT
- Bug fix or branch of new logic (error path, empty input, boundary) with no test covering it — regression risk. IMPROVEMENT
- Test deleted, `[Ignore]`/`Skip` added, or assertion loosened in the same MR as a behaviour change — hides a regression. IMPORTANT

## Sources

- https://raw.githubusercontent.com/davidfowl/AspNetCoreDiagnosticScenarios/master/AsyncGuidance.md
- https://learn.microsoft.com/en-us/aspnet/core/fundamentals/best-practices
- https://learn.microsoft.com/en-us/dotnet/core/extensions/dependency-injection-guidelines
- https://learn.microsoft.com/en-us/ef/core/performance/efficient-querying
- https://learn.microsoft.com/en-us/dotnet/fundamentals/code-analysis/quality-rules/ca1031
- https://learn.microsoft.com/en-us/dotnet/standard/design-guidelines/exception-throwing
- https://learn.microsoft.com/en-us/dotnet/core/extensions/httpclient-factory
- https://learn.microsoft.com/en-us/dotnet/core/extensions/logger-message-generator
- https://learn.microsoft.com/en-us/dotnet/csharp/nullable-references
- https://learn.microsoft.com/en-us/dotnet/csharp/fundamentals/coding-style/coding-conventions
