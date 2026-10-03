<?php
// Isolated SQLite fixture. Never connects to or changes the shared MySQL database.
$file=dirname(__DIR__).'/storage/demo.sqlite';
if(file_exists($file)) {echo "Demo database already exists; kept unchanged.\n";exit(0);}
if(!is_dir(dirname($file)))mkdir(dirname($file),0775,true);
touch($file);
putenv('DB_CONNECTION=sqlite');putenv('DB_DATABASE='.$file);
require dirname(__DIR__).'/vendor/autoload.php';
$app=require dirname(__DIR__).'/bootstrap/app.php';
$app->make(Illuminate\Contracts\Console\Kernel::class)->bootstrap();
use Illuminate\Support\Facades\DB;
DB::transaction(function(){
 foreach([
  'CREATE TABLE users (id INTEGER PRIMARY KEY, email TEXT UNIQUE, full_name TEXT, password_hash TEXT, role TEXT, campus TEXT)',
  'CREATE TABLE hubs (id INTEGER PRIMARY KEY, name TEXT, campus TEXT, location_detail TEXT, staff_in_charge TEXT, contact_phone TEXT, operating_hours TEXT)',
  'CREATE TABLE lockers (id INTEGER PRIMARY KEY, hub_id INTEGER, locker_code TEXT, size_type TEXT, status TEXT, current_order_id INTEGER NULL)',
  'CREATE TABLE escrow_orders (id INTEGER PRIMARY KEY, order_code TEXT UNIQUE, seller_id INTEGER, buyer_id INTEGER, hub_id INTEGER, locker_id INTEGER NULL, status TEXT, updated_at TEXT)',
  'CREATE TABLE hub_access_tokens (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, token_hash TEXT UNIQUE, expires_at TEXT, created_at TEXT)',
  'CREATE TABLE hub_events (id INTEGER PRIMARY KEY AUTOINCREMENT, order_id INTEGER, locker_id INTEGER, staff_id INTEGER, action TEXT, created_at TEXT)',
 ] as $sql)DB::statement($sql);
 foreach([1=>['seller@hunre.edu.vn','Người bán demo','STUDENT'],2=>['buyer@hunre.edu.vn','Người mua demo','STUDENT'],4=>['hub.cs1@hunre.edu.vn','Nhân viên Hub demo','HUB_STAFF']] as $id=>$user) {
  DB::table('users')->insert(['id'=>$id,'email'=>$user[0],'full_name'=>$user[1],'password_hash'=>password_hash('password',PASSWORD_BCRYPT),'role'=>$user[2],'campus'=>'CS1_HA_NOI']);
 }
 DB::table('hubs')->insert(['id'=>1,'name'=>'Trạm Hub CS1 — DEMO','campus'=>'CS1_HA_NOI','location_detail'=>'Nhà A HUNRE','staff_in_charge'=>'Nhân viên demo','contact_phone'=>'02438370598','operating_hours'=>'08:00–17:30']);
 foreach([1=>'SMALL',2=>'MEDIUM',3=>'LARGE'] as $id=>$size)DB::table('lockers')->insert(['id'=>$id,'hub_id'=>1,'locker_code'=>"LOCKER-{$size}-01",'size_type'=>$size,'status'=>'EMPTY']);
 foreach([1,2,3] as $id)DB::table('escrow_orders')->insert(['id'=>$id,'order_code'=>"ORD-DEMO-{$id}",'seller_id'=>1,'buyer_id'=>2,'hub_id'=>1,'status'=>'ESCROW_LOCKED','updated_at'=>now()]);
});
echo "Created isolated demo database: {$file}\n";
