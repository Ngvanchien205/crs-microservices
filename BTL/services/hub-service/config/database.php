<?php
return [
 'default' => env('DB_CONNECTION','mysql'),
 'connections' => [
  'mysql' => ['driver'=>'mysql','host'=>env('DB_HOST','127.0.0.1'),'port'=>env('DB_PORT','3307'),'database'=>env('DB_DATABASE','hunre_ecommerce'),'username'=>env('DB_USERNAME','root'),'password'=>env('DB_PASSWORD','root'),'charset'=>'utf8mb4','collation'=>'utf8mb4_unicode_ci','prefix'=>'','strict'=>true],
  'sqlite' => ['driver'=>'sqlite','database'=>env('DB_DATABASE',':memory:'),'prefix'=>'','foreign_key_constraints'=>true],
 ],
 'migrations' => ['table'=>'hub_migrations','update_date_on_publish'=>true],
];
