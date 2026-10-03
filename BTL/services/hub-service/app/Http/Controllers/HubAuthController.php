<?php
namespace App\Http\Controllers;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;
class HubAuthController
{
 public function login(Request $request)
 {
  $input=$request->validate(['email'=>'required|email|max:100','password'=>'required|string|max:255']);
  $user=DB::table('users')->where('email',$input['email'])->first();
  abort_unless($user && password_verify($input['password'],$user->password_hash),401,'Email hoặc mật khẩu không đúng.');
  $token=bin2hex(random_bytes(32)); $expiry=now()->addHours(config('hub.token_hours'));
  DB::table('hub_access_tokens')->insert(['user_id'=>$user->id,'token_hash'=>hash('sha256',$token),'expires_at'=>$expiry,'created_at'=>now()]);
  return response()->json(['success'=>true,'token'=>$token,'token_type'=>'Bearer','expires_at'=>$expiry->toIso8601String(),
   'user'=>['id'=>$user->id,'full_name'=>$user->full_name,'role'=>$user->role,'campus'=>$user->campus]]);
 }
 public function logout(Request $request)
 {
  DB::table('hub_access_tokens')->where('token_hash',hash('sha256',$request->bearerToken()))->delete();
  return response()->json(['success'=>true,'message'=>'Đã đăng xuất Hub.']);
 }
}
