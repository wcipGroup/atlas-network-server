<?php
$to_email = 'tyrovolas@auth.gr';
$subject = 'ATLAS Warning';
$message = 'Warning! The value of conductivity is 1369.'; 
$headers = 'From: info@atlas.com';
mail($to_email,$subject,$message,$headers);
?>
