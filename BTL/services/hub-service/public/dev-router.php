<?php
// Local development only. Serves the two Hub screens without replacing Gateway.
$path=rawurldecode(parse_url($_SERVER['REQUEST_URI'],PHP_URL_PATH) ?? '/');
$frontend=realpath(__DIR__.'/../../../frontend');
if($path==='/') {header('Location: /staff/');exit;}
if($path==='/staff') {header('Location: /staff/');exit;}
$file=null;$allowedRoot=null;
if(str_starts_with($path,'/staff/')) {
 $allowedRoot=$frontend.DIRECTORY_SEPARATOR.'hub-staff-portal';
 $file=$allowedRoot.DIRECTORY_SEPARATOR.(substr($path,7) ?: 'index.html');
} elseif($path==='/pages/hub-qr.html' || str_starts_with($path,'/css/')) {
 $allowedRoot=$frontend.DIRECTORY_SEPARATOR.'student-portal';
 $file=$allowedRoot.DIRECTORY_SEPARATOR.ltrim($path,'/');
}
if($file!==null) {
 $resolved=realpath($file);
 if(!$resolved || !str_starts_with($resolved,$allowedRoot.DIRECTORY_SEPARATOR) || !is_file($resolved)){http_response_code(404);exit;}
 $mime=match(pathinfo($resolved,PATHINFO_EXTENSION)){'html'=>'text/html; charset=utf-8','css'=>'text/css; charset=utf-8',default=>'application/octet-stream'};
 header('Content-Type: '.$mime);readfile($resolved);exit;
}
require __DIR__.'/index.php';
