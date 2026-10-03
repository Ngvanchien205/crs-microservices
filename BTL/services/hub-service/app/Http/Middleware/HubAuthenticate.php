<?php
namespace App\Http\Middleware;
use Closure;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;
class HubAuthenticate
{
 public function handle(Request $request, Closure $next)
 {
  $token=$request->bearerToken();
  abort_unless($token,401,'Cần đăng nhập Hub.');
  $session=DB::table('hub_access_tokens')->where('token_hash',hash('sha256',$token))->where('expires_at','>',now())->first();
  abort_unless($session,401,'Phiên đăng nhập không hợp lệ hoặc hết hạn.');
  $user=DB::table('users')->where('id',$session->user_id)->first();
  abort_unless($user,401,'Tài khoản không tồn tại.');
  $request->attributes->set('hub_user',$user);
  return $next($request);
 }
}
