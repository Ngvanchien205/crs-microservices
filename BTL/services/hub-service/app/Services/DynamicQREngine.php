<?php
namespace App\Services;
class DynamicQREngine
{
 private string $secretKey;
 public function __construct(?string $secretKey=null,private int $timeStep=30)
 {
  $this->secretKey=$secretKey ?? (string)config('hub.qr_secret');
  if(strlen($this->secretKey)<32) throw new \RuntimeException('HUB_QR_SECRET must contain at least 32 characters.');
 }
 public function generateToken(string $orderCode,int $userId,string $role='BUYER'): array
 {
  $timestamp=now()->timestamp;
  $token=$this->sign($orderCode,$userId,$role,intdiv($timestamp,$this->timeStep));
  return ['order_code'=>$orderCode,'user_id'=>$userId,'role'=>$role,'token'=>$token,
   'expires_in_seconds'=>$this->timeStep-($timestamp%$this->timeStep),
   'qr_payload'=>"HUNRE:{$orderCode}:{$userId}:{$role}:{$token}"];
 }
 public function verifyToken(string $orderCode,int $userId,string $role,string $tokenToVerify): bool
 {
  return hash_equals($this->sign($orderCode,$userId,$role,intdiv(now()->timestamp,$this->timeStep)),$tokenToVerify);
 }
 private function sign(string $orderCode,int $userId,string $role,int $window): string
 {
  return strtoupper(substr(hash_hmac('sha256',"{$orderCode}|{$userId}|{$role}|{$window}",$this->secretKey),0,16));
 }
}
