<?php
namespace App\Http\Controllers;

use App\Services\DynamicQREngine;
use BaconQrCode\Renderer\ImageRenderer;
use BaconQrCode\Renderer\Image\SvgImageBackEnd;
use BaconQrCode\Renderer\RendererStyle\RendererStyle;
use BaconQrCode\Writer;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;

class HubController
{
 public function getHubs()
 {
  return response()->json(['success'=>true,'data'=>DB::table('hubs')->orderBy('id')->get()]);
 }

 public function getLockers(Request $request,?int $hubId=null)
 {
  $input=$request->validate(['hub_id'=>'sometimes|integer|min:1']);
  $hubId=$hubId ?? ($input['hub_id'] ?? 1);
  $this->authorizeStaff($request,$hubId);
  $lockers=DB::table('lockers')->leftJoin('escrow_orders','lockers.current_order_id','=','escrow_orders.id')
   ->where('lockers.hub_id',$hubId)->select('lockers.*','escrow_orders.order_code as current_order')->orderBy('lockers.id')->get();
  foreach($lockers as $locker) $locker->description=$this->lockerDescription($locker->size_type);
  return response()->json(['success'=>true,'data'=>$lockers,'lockers'=>$lockers]);
 }

 public function getOrder(Request $request,string $orderCode)
 {
  $order=$this->order($orderCode);
  $user=$request->attributes->get('hub_user');
  if(in_array($user->role,['HUB_STAFF','ADMIN'],true)) $this->authorizeStaff($request,$order->hub_id);
  else abort_unless(in_array((int)$user->id,[(int)$order->seller_id,(int)$order->buyer_id],true),403,'Không có quyền xem đơn này.');
  return response()->json(['success'=>true,'data'=>$order,'order'=>$order]);
 }

 public function generateDynamicQR(Request $request,string $orderCode,DynamicQREngine $qrEngine)
 {
  $input=$request->validate(['role'=>'sometimes|in:BUYER,SELLER','user_id'=>'sometimes|integer|min:1']);
  $order=$this->order($orderCode);
  $user=$request->attributes->get('hub_user');
  $role=$input['role'] ?? 'BUYER';
  $ownerId=$role==='SELLER' ? $order->seller_id : $order->buyer_id;
  abort_unless((int)$ownerId===(int)$user->id,403,'Chỉ chủ đơn tương ứng được tạo mã QR.');
  abort_if(isset($input['user_id']) && (int)$input['user_id']!==(int)$user->id,403,'Không được giả mạo user_id.');
  $expected=$role==='SELLER' ? 'ESCROW_LOCKED' : 'STORED_AT_HUB';
  abort_unless($order->status===$expected,409,'Đơn hàng chưa sẵn sàng cho thao tác này.');
  $data=$qrEngine->generateToken($orderCode,(int)$user->id,$role);
  $writer=new Writer(new ImageRenderer(new RendererStyle(220),new SvgImageBackEnd()));
  $data['qr_image_url']='data:image/svg+xml;base64,'.base64_encode($writer->writeString($data['qr_payload']));
  return response()->json(['success'=>true,'data'=>$data])->header('Cache-Control','no-store');
 }

 public function processCheckin(Request $request,DynamicQREngine $qrEngine)
 {
  return $this->transfer($request,$qrEngine,true);
 }
 public function processCheckout(Request $request,DynamicQREngine $qrEngine)
 {
  return $this->transfer($request,$qrEngine,false);
 }

 private function transfer(Request $request,DynamicQREngine $qrEngine,bool $checkin)
 {
  $actorField=$checkin ? 'seller_id' : 'buyer_id';
  $role=$checkin ? 'SELLER' : 'BUYER';
  // The scanner can submit a full QR payload or the original DTO fields.
  if($request->filled('qr_payload')) {
   $payload=$request->validate(['qr_payload'=>'required|string|max:200'])['qr_payload'];
   abort_unless(preg_match('/^HUNRE:([A-Za-z0-9_-]{1,50}):([1-9][0-9]*):(BUYER|SELLER):([A-F0-9]{16})$/D',$payload,$parts),422,'Mã QR sai định dạng.');
   abort_unless($parts[3]===$role,422,'Mã QR không đúng loại bàn giao.');
   foreach(['order_code'=>$parts[1],$actorField=>(int)$parts[2],'token'=>$parts[4]] as $key=>$value) {
    abort_if($request->has($key) && (string)$request->input($key)!==(string)$value,422,'Mã QR và dữ liệu nhập không khớp.');
    $request->merge([$key=>$value]);
   }
  }
  $input=$request->validate(['order_code'=>'required|string|max:50','token'=>'required|string|regex:/^[A-F0-9]{16}$/D',
   $actorField=>'required|integer|min:1','size_type'=>'nullable|in:SMALL,MEDIUM,LARGE','scan_type'=>'sometimes|in:CHECKIN,CHECKOUT']);
  abort_if(isset($input['scan_type']) && $input['scan_type']!==($checkin?'CHECKIN':'CHECKOUT'),422,'Loại thao tác không khớp.');
  $result=DB::transaction(function () use($request,$qrEngine,$input,$actorField,$role,$checkin) {
   $order=$this->order($input['order_code'],true);
   $staff=$this->authorizeStaff($request,$order->hub_id);
   abort_unless((int)$order->{$actorField}===(int)$input[$actorField],403,'Người bàn giao không thuộc đơn hàng.');
   abort_unless($qrEngine->verifyToken($order->order_code,(int)$input[$actorField],$role,$input['token']),400,'Mã QR hết hạn hoặc không hợp lệ.');
   abort_unless($order->status===($checkin?'ESCROW_LOCKED':'STORED_AT_HUB'),409,'Đơn đã xử lý hoặc không đúng trạng thái.');
   if($checkin) {
    abort_if($order->locker_id!==null,409,'Đơn đã được gán ô tủ.');
    $query=DB::table('lockers')->where('hub_id',$order->hub_id)->where('status','EMPTY')->whereNull('current_order_id');
    if(!empty($input['size_type'])) $query->where('size_type',$input['size_type']);
    $locker=$query->orderBy('id')->lockForUpdate()->first();
    abort_unless($locker,409,'Không còn ô tủ trống phù hợp tại trạm.');
    DB::table('lockers')->where('id',$locker->id)->update(['status'=>'OCCUPIED','current_order_id'=>$order->id]);
    $state='STORED_AT_HUB';
   } else {
    $locker=DB::table('lockers')->where('id',$order->locker_id)->lockForUpdate()->first();
    abort_unless($locker && (int)$locker->hub_id===(int)$order->hub_id && $locker->status==='OCCUPIED' && (int)$locker->current_order_id===(int)$order->id,409,'Ô tủ không khớp đơn hàng; không mở tủ.');
    DB::table('lockers')->where('id',$locker->id)->update(['status'=>'EMPTY','current_order_id'=>null]);
    $state='INSPECTING_AT_HUB';
   }
   DB::table('escrow_orders')->where('id',$order->id)->update(['locker_id'=>$checkin?$locker->id:null,'status'=>$state,'updated_at'=>now()]);
   DB::table('hub_events')->insert(['order_id'=>$order->id,'locker_id'=>$locker->id,'staff_id'=>$staff->id,'action'=>$checkin?'CHECKIN':'CHECKOUT','created_at'=>now()]);
   return ['success'=>true,'message'=>$checkin?'Người bán check-in thành công!':'Đã bàn giao cho người mua kiểm tra tại Hub. Chưa giải ngân ký quỹ.',
    'order_code'=>$order->order_code,'status'=>$state,'locker_code'=>$locker->locker_code,
    'locker'=>array_merge((array)$locker,['status'=>$checkin?'OCCUPIED':'EMPTY','current_order_id'=>$checkin?$order->id:null,'current_order'=>$checkin?$order->order_code:null,'description'=>$this->lockerDescription($locker->size_type)]),
    'instruction'=>$checkin?"Dán tem {$order->order_code} và cất vào {$locker->locker_code}.":'Mời người mua kiểm tra hàng trước khi xác nhận với Escrow.'];
  },3);
  return response()->json($result);
 }

 private function order(string $orderCode,bool $lock=false): object
 {
  $query=DB::table('escrow_orders')->where('order_code',$orderCode);
  if($lock) $query->lockForUpdate();
  $order=$query->first();
  abort_unless($order,404,'Không tìm thấy đơn hàng.');
  return $order;
 }

 private function lockerDescription(string $size): string
 {
  return match($size){'SMALL'=>'Cỡ nhỏ (giáo trình, sách)','LARGE'=>'Cỡ lớn (màn hình, case)',default=>'Cỡ vừa (thiết bị học tập)'};
 }

 private function authorizeStaff(Request $request,int $hubId): object
 {
  $user=$request->attributes->get('hub_user');
  abort_unless(in_array($user->role,['HUB_STAFF','ADMIN'],true),403,'Chỉ nhân viên Hub hoặc quản trị viên được thao tác.');
  $hub=DB::table('hubs')->where('id',$hubId)->first();
  abort_unless($hub,404,'Không tìm thấy trạm Hub.');
  abort_unless($user->role==='ADMIN' || $user->campus===$hub->campus,403,'Trạm Hub nằm ngoài cơ sở được phân công.');
  return $user;
 }
}
