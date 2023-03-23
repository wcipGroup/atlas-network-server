<?php 
$to = 'tyrovolas@auth.gr';
$subject = 'ATLAS Warning';
$message = 'Warning! The value of';
$headers = 'From: info@atlas.com';
if(mail($to,$subject,$message,$headers))
{
echo "Email was sent successfully.\r\n";
}
else{
echo "Email was not sent. <br />";
}
?>
