<?php
use Illuminate\Foundation\Application;
use Illuminate\Foundation\Configuration\Exceptions;
use Illuminate\Foundation\Configuration\Middleware;
use Illuminate\Http\Request;
foreach (['bootstrap/cache','storage/framework/cache/data','storage/framework/sessions','storage/framework/views','storage/logs'] as $path) {
    if (!is_dir(dirname(__DIR__).'/'.$path)) mkdir(dirname(__DIR__).'/'.$path, 0775, true);
}
return Application::configure(basePath: dirname(__DIR__))
    ->withRouting(api: __DIR__.'/../routes/api.php', health: '/up')
    ->withMiddleware(function (Middleware $middleware) {
        $middleware->alias(['hub.auth' => App\Http\Middleware\HubAuthenticate::class]);
    })
    ->withExceptions(function (Exceptions $exceptions) {
        $exceptions->shouldRenderJsonWhen(fn (Request $request, Throwable $error) => true);
        $exceptions->respond(function ($response) {
            if ($response->getStatusCode() >= 400) {
                $body = json_decode($response->getContent(), true) ?: [];
                $response->setData(['success' => false] + $body);
            }
            return $response;
        });
    })->create();
