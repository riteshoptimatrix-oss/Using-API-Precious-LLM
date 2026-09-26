<?php
/*
================================================================================
SQL Table Creation & Migration Query for Bill Export Feature with OCR
Copy and paste the following query directly into MySQL / phpMyAdmin:

CREATE TABLE IF NOT EXISTS `bill_export` (
  `id` INT(11) NOT NULL AUTO_INCREMENT,
  `user_id` INT(11) NOT NULL DEFAULT 0,
  `original_name` VARCHAR(255) NOT NULL,
  `file_path` VARCHAR(255) NOT NULL,
  `file_type` VARCHAR(100) NOT NULL,
  `file_size` BIGINT(20) NOT NULL DEFAULT 0,
  `status` VARCHAR(50) DEFAULT 'active',
  `ocr_status` VARCHAR(50) DEFAULT 'pending',
  `vendor_name` VARCHAR(255) DEFAULT NULL,
  `bill_number` VARCHAR(100) DEFAULT NULL,
  `bill_date` VARCHAR(50) DEFAULT NULL,
  `due_date` VARCHAR(50) DEFAULT NULL,
  `currency` VARCHAR(20) DEFAULT 'INR',
  `subtotal` VARCHAR(50) DEFAULT NULL,
  `tax_amount` VARCHAR(50) DEFAULT NULL,
  `total_amount` VARCHAR(50) DEFAULT NULL,
  `payment_status` VARCHAR(50) DEFAULT NULL,
  `ocr_summary` TEXT DEFAULT NULL,
  `ocr_data` LONGTEXT DEFAULT NULL,
  `ocr_text` LONGTEXT DEFAULT NULL,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  KEY `ocr_status` (`ocr_status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Migration for existing table:
-- ALTER TABLE `bill_export` ADD COLUMN IF NOT EXISTS `ocr_status` VARCHAR(50) DEFAULT 'pending';
-- ALTER TABLE `bill_export` ADD COLUMN IF NOT EXISTS `vendor_name` VARCHAR(255) DEFAULT NULL;
-- ALTER TABLE `bill_export` ADD COLUMN IF NOT EXISTS `bill_number` VARCHAR(100) DEFAULT NULL;
-- ALTER TABLE `bill_export` ADD COLUMN IF NOT EXISTS `bill_date` VARCHAR(50) DEFAULT NULL;
-- ALTER TABLE `bill_export` ADD COLUMN IF NOT EXISTS `due_date` VARCHAR(50) DEFAULT NULL;
-- ALTER TABLE `bill_export` ADD COLUMN IF NOT EXISTS `currency` VARCHAR(20) DEFAULT 'INR';
-- ALTER TABLE `bill_export` ADD COLUMN IF NOT EXISTS `subtotal` VARCHAR(50) DEFAULT NULL;
-- ALTER TABLE `bill_export` ADD COLUMN IF NOT EXISTS `tax_amount` VARCHAR(50) DEFAULT NULL;
-- ALTER TABLE `bill_export` ADD COLUMN IF NOT EXISTS `total_amount` VARCHAR(50) DEFAULT NULL;
-- ALTER TABLE `bill_export` ADD COLUMN IF NOT EXISTS `payment_status` VARCHAR(50) DEFAULT NULL;
-- ALTER TABLE `bill_export` ADD COLUMN IF NOT EXISTS `ocr_summary` TEXT DEFAULT NULL;
-- ALTER TABLE `bill_export` ADD COLUMN IF NOT EXISTS `ocr_data` LONGTEXT DEFAULT NULL;
-- ALTER TABLE `bill_export` ADD COLUMN IF NOT EXISTS `ocr_text` LONGTEXT DEFAULT NULL;
-- ALTER TABLE `bill_export` ADD COLUMN IF NOT EXISTS `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP;
================================================================================
*/

class model_bill_export {
	public $fields = array();
	public $nullable = array();
	public $default_value = array();
	public $ID = 0;
	public $KEY = "";

	function __CONSTRUCT($ID=0){
		$this->ID = $ID;
		$this->KEY = "id";

		// Basic file fields
		$this->fields["id"] = "int(11)";
		$this->nullable["id"] = "NO";
		$this->default_value["id"] = "";

		$this->fields["user_id"] = "int(11)";
		$this->nullable["user_id"] = "NO";
		$this->default_value["user_id"] = "0";

		$this->fields["original_name"] = "varchar(255)";
		$this->nullable["original_name"] = "NO";
		$this->default_value["original_name"] = "";

		$this->fields["file_path"] = "varchar(255)";
		$this->nullable["file_path"] = "NO";
		$this->default_value["file_path"] = "";

		$this->fields["file_type"] = "varchar(100)";
		$this->nullable["file_type"] = "NO";
		$this->default_value["file_type"] = "";

		$this->fields["file_size"] = "bigint(20)";
		$this->nullable["file_size"] = "NO";
		$this->default_value["file_size"] = "0";

		$this->fields["status"] = "varchar(50)";
		$this->nullable["status"] = "NO";
		$this->default_value["status"] = "active";

		// OCR Extracted Fields
		$this->fields["ocr_status"] = "varchar(50)";
		$this->nullable["ocr_status"] = "NO";
		$this->default_value["ocr_status"] = "pending";

		$this->fields["vendor_name"] = "varchar(255)";
		$this->nullable["vendor_name"] = "YES";
		$this->default_value["vendor_name"] = "";

		$this->fields["bill_number"] = "varchar(100)";
		$this->nullable["bill_number"] = "YES";
		$this->default_value["bill_number"] = "";

		$this->fields["bill_date"] = "varchar(50)";
		$this->nullable["bill_date"] = "YES";
		$this->default_value["bill_date"] = "";

		$this->fields["due_date"] = "varchar(50)";
		$this->nullable["due_date"] = "YES";
		$this->default_value["due_date"] = "";

		$this->fields["currency"] = "varchar(20)";
		$this->nullable["currency"] = "YES";
		$this->default_value["currency"] = "INR";

		$this->fields["subtotal"] = "varchar(50)";
		$this->nullable["subtotal"] = "YES";
		$this->default_value["subtotal"] = "";

		$this->fields["tax_amount"] = "varchar(50)";
		$this->nullable["tax_amount"] = "YES";
		$this->default_value["tax_amount"] = "";

		$this->fields["total_amount"] = "varchar(50)";
		$this->nullable["total_amount"] = "YES";
		$this->default_value["total_amount"] = "";

		$this->fields["payment_status"] = "varchar(50)";
		$this->nullable["payment_status"] = "YES";
		$this->default_value["payment_status"] = "";

		$this->fields["ocr_summary"] = "text";
		$this->nullable["ocr_summary"] = "YES";
		$this->default_value["ocr_summary"] = "";

		$this->fields["ocr_data"] = "longtext";
		$this->nullable["ocr_data"] = "YES";
		$this->default_value["ocr_data"] = "";

		$this->fields["ocr_text"] = "longtext";
		$this->nullable["ocr_text"] = "YES";
		$this->default_value["ocr_text"] = "";

		$this->fields["created_at"] = "datetime";
		$this->nullable["created_at"] = "YES";
		$this->default_value["created_at"] = "CURRENT_TIMESTAMP";

		$this->fields["updated_at"] = "datetime";
		$this->nullable["updated_at"] = "YES";
		$this->default_value["updated_at"] = "CURRENT_TIMESTAMP";
	}
}
?>
