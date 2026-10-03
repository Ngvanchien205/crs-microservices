<?php
namespace App\Providers;
use Illuminate\Support\ServiceProvider;
use Illuminate\Support\Facades\RateLimiter;
use Illuminate\Cache\RateLimiting\Limit;
class AppServiceProvider extends ServiceProvider
{
 public function boot(): void
 {
  RateLimiter::for('hub-login',fn($request)=>Limit::perMinute(5)->by('login:'.$request->ip()));
  RateLimiter::for('hub-api',fn($request)=>Limit::perMinute(120)->by('api:'.hash('sha256',$request->bearerToken() ?? $request->ip())));
 }
}
