<?php
namespace Tests;

use App\Services\DynamicQREngine;
use Illuminate\Foundation\Testing\TestCase;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Schema;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Carbon;

class HubTest extends TestCase
{
 protected function setUp(): void
 {
  parent::setUp();
  config(['cache.default'=>'array','cache.stores.array'=>['driver'=>'array']]);
  config(['logging.default'=>'null','logging.channels.null'=>['driver'=>'monolog','handler'=>\Monolog\Handler\NullHandler::class]]);
  Carbon::setTestNow('2026-10-03 10:00:00');
  Schema::create('users',function(Blueprint $t){$t->id();$t->string('email');$t->string('full_name');$t->string('password_hash');$t->string('role');$t->string('campus');});
  Schema::create('hubs',function(Blueprint $t){$t->id();$t->string('name');$t->string('campus');});
  Schema::create('lockers',function(Blueprint $t){$t->id();$t->unsignedBigInteger('hub_id');$t->string('locker_code');$t->string('size_type');$t->string('status');$t->unsignedBigInteger('current_order_id')->nullable();});
  Schema::create('escrow_orders',function(Blueprint $t){$t->id();$t->string('order_code')->unique();$t->unsignedBigInteger('seller_id');$t->unsignedBigInteger('buyer_id');$t->unsignedBigInteger('hub_id');$t->unsignedBigInteger('locker_id')->nullable();$t->string('status');$t->timestamp('updated_at')->nullable();});
  Schema::create('hub_access_tokens',function(Blueprint $t){$t->id();$t->unsignedBigInteger('user_id');$t->string('token_hash')->unique();$t->timestamp('expires_at');$t->timestamp('created_at');});
  Schema::create('hub_events',function(Blueprint $t){$t->id();$t->unsignedBigInteger('order_id');$t->unsignedBigInteger('locker_id');$t->unsignedBigInteger('staff_id');$t->string('action');$t->timestamp('created_at');});
  foreach([1=>'STUDENT',2=>'STUDENT',3=>'STUDENT',4=>'HUB_STAFF',5=>'ADMIN',6=>'HUB_STAFF'] as $id=>$role) {
   DB::table('users')->insert(['id'=>$id,'email'=>"user{$id}@hunre.edu.vn",'full_name'=>"User {$id}",'password_hash'=>password_hash('password',PASSWORD_BCRYPT,['cost'=>4]),'role'=>$role,'campus'=>$id===6?'CS2_THANH_HOA':'CS1_HA_NOI']);
  }
  DB::table('hubs')->insert(['id'=>1,'name'=>'CS1','campus'=>'CS1_HA_NOI']);
  foreach([1=>'SMALL',2=>'MEDIUM',3=>'LARGE'] as $id=>$size) DB::table('lockers')->insert(['id'=>$id,'hub_id'=>1,'locker_code'=>"L{$id}",'size_type'=>$size,'status'=>'EMPTY']);
  DB::table('escrow_orders')->insert(['id'=>1,'order_code'=>'ORD-TEST-1','seller_id'=>1,'buyer_id'=>2,'hub_id'=>1,'status'=>'ESCROW_LOCKED']);
 }

 protected function tearDown(): void { Carbon::setTestNow();parent::tearDown(); }
 private function token(int $id=4): string
 {
  $token="test-token-{$id}";
  DB::table('hub_access_tokens')->updateOrInsert(['token_hash'=>hash('sha256',$token)],['user_id'=>$id,'expires_at'=>now()->addHour(),'created_at'=>now()]);
  return $token;
 }
 private function payload(string $role='SELLER',?int $id=null): array
 {
  $id=$id ?? ($role==='SELLER'?1:2);
  return ['order_code'=>'ORD-TEST-1','token'=>(new DynamicQREngine)->generateToken('ORD-TEST-1',$id,$role)['token'],$role==='SELLER'?'seller_id':'buyer_id'=>$id];
 }
 private function checkin(): void
 {
  $this->withToken($this->token())->postJson('/api/v1/hub/checkin',$this->payload()+['size_type'=>'MEDIUM'])->assertOk()->assertJsonPath('locker_code','L2');
 }
 public function test_health_stations_and_locker_aliases(): void
 {
  $this->getJson('/up')->assertOk();
  $this->getJson('/api/v1/hub/stations')->assertOk()->assertJsonPath('data.0.id',1);
  $this->getJson('/api/v1/hub/lockers')->assertUnauthorized();
  $this->withToken($this->token())->getJson('/api/v1/hub/lockers/1')->assertOk()->assertJsonCount(3,'lockers')->assertJsonCount(3,'data');
  $this->withToken($this->token())->getJson('/api/v1/hub/lockers/not-a-number')->assertNotFound();
 }
 public function test_login_logout_and_expiry(): void
 {
  $this->postJson('/api/v1/hub/auth/login',['email'=>'user4@hunre.edu.vn','password'=>'wrong'])->assertUnauthorized();
  $login=$this->postJson('/api/v1/hub/auth/login',['email'=>'user4@hunre.edu.vn','password'=>'password'])->assertOk();
  $token=$login->json('token');$this->assertNotEmpty($token);
  $this->assertDatabaseHas('hub_access_tokens',['token_hash'=>hash('sha256',$token)]);
  $this->withToken($token)->postJson('/api/v1/hub/auth/logout')->assertOk();
  $this->withToken($token)->getJson('/api/v1/hub/lockers')->assertUnauthorized();
  $token=$this->token();Carbon::setTestNow(now()->addHours(2));
  $this->withToken($token)->getJson('/api/v1/hub/lockers')->assertUnauthorized();
 }
 public function test_login_rate_limit(): void
 {
  for($i=0;$i<5;$i++)$this->postJson('/api/v1/hub/auth/login',['email'=>'user4@hunre.edu.vn','password'=>'wrong'])->assertUnauthorized();
  $this->postJson('/api/v1/hub/auth/login',['email'=>'user4@hunre.edu.vn','password'=>'wrong'])->assertStatus(429);
 }
 public function test_student_and_other_campus_cannot_scan(): void
 {
  $this->withToken($this->token(1))->postJson('/api/v1/hub/checkin',$this->payload())->assertForbidden();
  $this->withToken($this->token(6))->postJson('/api/v1/hub/checkin',$this->payload())->assertForbidden();
  $this->assertDatabaseHas('escrow_orders',['id'=>1,'status'=>'ESCROW_LOCKED']);
 }
 public function test_qr_ownership_state_and_local_image(): void
 {
  $uri='/api/v1/hub/orders/ORD-TEST-1/dynamic-qr?role=SELLER';
  $this->withToken($this->token(3))->getJson($uri)->assertForbidden();
  $this->withToken($this->token(4))->getJson($uri)->assertForbidden();
  $this->withToken($this->token(1))->getJson($uri.'&user_id=2')->assertForbidden();
  $response=$this->withToken($this->token(1))->getJson($uri)->assertOk()->assertHeader('Cache-Control','no-store, private');
  $this->assertStringStartsWith('data:image/svg+xml;base64,',$response->json('data.qr_image_url'));
  $this->assertStringContainsString(':1:SELLER:',$response->json('data.qr_payload'));
  $this->withToken($this->token(2))->getJson('/api/v1/hub/orders/ORD-TEST-1/dynamic-qr?role=BUYER')->assertStatus(409);
 }
 public function test_checkin_checkout_and_replay(): void
 {
  $this->checkin();
  $this->withToken($this->token())->getJson('/api/v1/hub/lockers')->assertJsonPath('lockers.1.current_order','ORD-TEST-1');
  $this->assertDatabaseHas('lockers',['id'=>2,'status'=>'OCCUPIED','current_order_id'=>1]);
  $this->assertDatabaseHas('escrow_orders',['id'=>1,'status'=>'STORED_AT_HUB','locker_id'=>2]);
  $this->withToken($this->token())->postJson('/api/v1/hub/scan-checkin',$this->payload())->assertStatus(409);
  $this->withToken($this->token())->postJson('/api/v1/hub/scan-checkout',$this->payload('BUYER'))->assertOk()->assertJsonPath('status','INSPECTING_AT_HUB')->assertJsonPath('locker.locker_code','L2')->assertJsonPath('locker.status','EMPTY');
  $this->assertDatabaseHas('lockers',['id'=>2,'status'=>'EMPTY','current_order_id'=>null]);
  $this->assertDatabaseHas('escrow_orders',['id'=>1,'status'=>'INSPECTING_AT_HUB','locker_id'=>null]);
  $this->withToken($this->token())->postJson('/api/v1/hub/checkout',$this->payload('BUYER'))->assertStatus(409);
  $this->assertDatabaseCount('hub_events',2);
 }
 public function test_invalid_expired_qr_and_wrong_actor_do_not_mutate(): void
 {
  $data=$this->payload();$data['token']='0000000000000000';
  $this->withToken($this->token())->postJson('/api/v1/hub/checkin',$data)->assertStatus(400);
  $data=$this->payload();Carbon::setTestNow(now()->addSeconds(30));
  $this->withToken($this->token())->postJson('/api/v1/hub/checkin',$data)->assertStatus(400);
  $this->withToken($this->token())->postJson('/api/v1/hub/checkin',$this->payload('SELLER',3))->assertForbidden();
  $this->assertDatabaseCount('hub_events',0);
  $this->assertDatabaseHas('escrow_orders',['id'=>1,'status'=>'ESCROW_LOCKED']);
 }
 public function test_full_size_unavailable_and_wrong_state(): void
 {
  DB::table('lockers')->where('id',2)->update(['status'=>'MAINTENANCE']);
  $this->withToken($this->token())->postJson('/api/v1/hub/checkin',$this->payload()+['size_type'=>'MEDIUM'])->assertStatus(409);
  DB::table('lockers')->update(['status'=>'OCCUPIED']);
  $this->withToken($this->token())->postJson('/api/v1/hub/checkin',$this->payload())->assertStatus(409);
  DB::table('escrow_orders')->where('id',1)->update(['status'=>'INITIATED']);
  $this->withToken($this->token())->postJson('/api/v1/hub/checkin',$this->payload())->assertStatus(409);
  $this->assertDatabaseCount('hub_events',0);
 }
 public function test_checkout_never_frees_another_orders_locker(): void
 {
  $this->checkin();DB::table('lockers')->where('id',2)->update(['current_order_id'=>99]);
  $this->withToken($this->token())->postJson('/api/v1/hub/checkout',$this->payload('BUYER'))->assertStatus(409);
  $this->assertDatabaseHas('lockers',['id'=>2,'status'=>'OCCUPIED','current_order_id'=>99]);
  $this->assertDatabaseHas('escrow_orders',['id'=>1,'status'=>'STORED_AT_HUB']);
 }
 public function test_audit_failure_rolls_back_entire_transfer(): void
 {
  DB::statement("CREATE TRIGGER reject_audit BEFORE INSERT ON hub_events BEGIN SELECT RAISE(ABORT,'audit failure'); END");
  $this->withToken($this->token())->postJson('/api/v1/hub/checkin',$this->payload())->assertStatus(500);
  $this->assertDatabaseHas('escrow_orders',['id'=>1,'status'=>'ESCROW_LOCKED','locker_id'=>null]);
  $this->assertDatabaseHas('lockers',['id'=>1,'status'=>'EMPTY','current_order_id'=>null]);
 }
 public function test_full_qr_payload_validation(): void
 {
  $qr=(new DynamicQREngine)->generateToken('ORD-TEST-1',1,'SELLER');
  $this->withToken($this->token())->postJson('/api/v1/hub/checkin',['qr_payload'=>$qr['qr_payload'],'order_code'=>'DIFFERENT'])->assertUnprocessable();
  $this->withToken($this->token())->postJson('/api/v1/hub/checkout',['qr_payload'=>$qr['qr_payload']])->assertUnprocessable();
  $this->withToken($this->token())->postJson('/api/v1/hub/checkin',['qr_payload'=>$qr['qr_payload'],'scan_type'=>'CHECKIN'])->assertOk();
 }
 public function test_missing_order_and_invalid_input(): void
 {
  $this->withToken($this->token())->getJson('/api/v1/hub/orders/MISSING')->assertNotFound();
  $this->withToken($this->token())->postJson('/api/v1/hub/checkin',[])->assertUnprocessable();
  $this->withToken($this->token(3))->getJson('/api/v1/hub/orders/ORD-TEST-1')->assertForbidden();
 }
}
