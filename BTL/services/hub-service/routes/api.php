<?php
use Illuminate\Support\Facades\Route;
use App\Http\Controllers\HubController;
use App\Http\Controllers\HubAuthController;
Route::prefix('v1/hub')->group(function () {
 Route::post('/auth/login',[HubAuthController::class,'login'])->middleware('throttle:hub-login');
 Route::get('/stations',[HubController::class,'getHubs']);
 Route::middleware(['hub.auth','throttle:hub-api'])->group(function () {
  Route::post('/auth/logout',[HubAuthController::class,'logout']);
  Route::get('/lockers/{hubId?}',[HubController::class,'getLockers'])->whereNumber('hubId');
  Route::get('/orders/{orderCode}',[HubController::class,'getOrder']);
  Route::get('/orders/{orderCode}/dynamic-qr',[HubController::class,'generateDynamicQR']);
  Route::post('/scan-checkin',[HubController::class,'processCheckin']);
  Route::post('/checkin',[HubController::class,'processCheckin']);
  Route::post('/scan-checkout',[HubController::class,'processCheckout']);
  Route::post('/checkout',[HubController::class,'processCheckout']);
 });
});
