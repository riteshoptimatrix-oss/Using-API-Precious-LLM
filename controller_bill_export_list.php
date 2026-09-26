<?php
/*
================================================================================
Controller for Bill Export & OCR Feature
Integrated with Gemini Multimodal AI Backend
================================================================================
*/

class _bill_export_list extends controller {

	// Backend OCR API Endpoint (FastAPI Python backend)
	private $ocr_backend_url = "http://127.0.0.1:8000/api/ocr/bill";

	function init() {}

	function onload() {
		$act = $this->app->getCurrentAction();
		if ($act == "reprocess_ocr") {
			$this->reprocess_ocr();
		} else if ($act == "get_ocr_details") {
			$this->get_ocr_details();
		} else if ($act == "upload_bill") {
			$this->upload_bill();
		} else if ($act == "delete_bill") {
			$this->delete_bill();
		} else if ($act == "") {
			$this->load_data();
		}
	}

	/**
	 * Ensures the bill_export table exists and has all required OCR columns.
	 */
	private function ensure_table_schema($conn) {
		$create_sql = "CREATE TABLE IF NOT EXISTS `bill_export` (
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
		) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;";
		@mysqli_query($conn, $create_sql);

		// Check and auto-migrate any missing columns in existing table
		$res_cols = @mysqli_query($conn, "SHOW COLUMNS FROM `bill_export`");
		$existing_cols = array();
		if ($res_cols) {
			while ($c = mysqli_fetch_assoc($res_cols)) {
				$existing_cols[] = strtolower($c['Field']);
			}
		}

		$needed_columns = array(
			'ocr_status'     => "VARCHAR(50) DEFAULT 'pending'",
			'vendor_name'    => "VARCHAR(255) DEFAULT NULL",
			'bill_number'    => "VARCHAR(100) DEFAULT NULL",
			'bill_date'      => "VARCHAR(50) DEFAULT NULL",
			'due_date'       => "VARCHAR(50) DEFAULT NULL",
			'currency'       => "VARCHAR(20) DEFAULT 'INR'",
			'subtotal'       => "VARCHAR(50) DEFAULT NULL",
			'tax_amount'     => "VARCHAR(50) DEFAULT NULL",
			'total_amount'   => "VARCHAR(50) DEFAULT NULL",
			'payment_status' => "VARCHAR(50) DEFAULT NULL",
			'ocr_summary'    => "TEXT DEFAULT NULL",
			'ocr_data'       => "LONGTEXT DEFAULT NULL",
			'ocr_text'       => "LONGTEXT DEFAULT NULL",
			'updated_at'     => "DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"
		);

		foreach ($needed_columns as $col => $definition) {
			if (!in_array($col, $existing_cols)) {
				@mysqli_query($conn, "ALTER TABLE `bill_export` ADD COLUMN `$col` $definition");
			}
		}
	}

	/**
	 * Main Listing & Filter method
	 */
	function load_data() {
		$conn = $this->app->objDB->getConnection();
		$this->ensure_table_schema($conn);

		$search_query = trim($this->app->getPostVar('search_query') ?? $this->app->getGetVar('search_query') ?? '');
		$file_category = trim($this->app->getPostVar('file_category') ?? $this->app->getGetVar('file_category') ?? '');
		$ocr_filter = trim($this->app->getPostVar('ocr_filter') ?? $this->app->getGetVar('ocr_filter') ?? '');

		$where_clauses = array("1=1");

		if (!empty($search_query)) {
			$escaped_search = mysqli_real_escape_string($conn, $search_query);
			$where_clauses[] = "(
				bill_export.original_name LIKE '%$escaped_search%' OR 
				bill_export.vendor_name LIKE '%$escaped_search%' OR 
				bill_export.bill_number LIKE '%$escaped_search%' OR 
				users.name LIKE '%$escaped_search%'
			)";
		}

		if (!empty($file_category)) {
			$escaped_cat = mysqli_real_escape_string($conn, $file_category);
			if ($escaped_cat == 'image') {
				$where_clauses[] = "(bill_export.file_type LIKE 'image/%' OR LOWER(bill_export.file_type) IN ('jpg','jpeg','png','gif','webp','bmp','svg'))";
			} else if ($escaped_cat == 'document') {
				$where_clauses[] = "(bill_export.file_type NOT LIKE 'image/%' AND LOWER(bill_export.file_type) NOT IN ('jpg','jpeg','png','gif','webp','bmp','svg'))";
			}
		}

		if (!empty($ocr_filter)) {
			$escaped_ocr = mysqli_real_escape_string($conn, $ocr_filter);
			$where_clauses[] = "bill_export.ocr_status = '$escaped_ocr'";
		}

		$where_sql = implode(" AND ", $where_clauses);

		$obj_model = $this->app->load_model("bill_export");
		$records_per_page = isset($_SESSION['records']) && intval($_SESSION['records']) > 0 ? intval($_SESSION['records']) : 50;
		$obj_model->set_paging_settings($records_per_page, 5);

		$sql = "SELECT bill_export.*, users.name as uploaded_by_name, users.email as uploaded_by_email 
				FROM bill_export 
				LEFT JOIN users ON bill_export.user_id = users.id 
				WHERE $where_sql 
				ORDER BY bill_export.created_at DESC, bill_export.id DESC";

		$this->app->objDB->setQuery($sql);
		$rs_bills = $this->app->objDB->execute("rs_bills", true, "bill_export.id");

		// Fetch summary metrics
		$total_files = 0;
		$total_images = 0;
		$total_docs = 0;
		$total_size = 0;
		$total_ocr_done = 0;
		$total_ocr_pending = 0;
		$total_billed_amount = 0.0;

		$res_stats = @mysqli_query($conn, "SELECT COUNT(*) as total_count, SUM(file_size) as sum_size FROM bill_export");
		if ($res_stats && $row_stats = mysqli_fetch_assoc($res_stats)) {
			$total_files = intval($row_stats['total_count']);
			$total_size = floatval($row_stats['sum_size']);
		}

		$res_imgs = @mysqli_query($conn, "SELECT COUNT(*) as img_count FROM bill_export WHERE file_type LIKE 'image/%' OR LOWER(file_type) IN ('jpg','jpeg','png','gif','webp','bmp','svg')");
		if ($res_imgs && $row_imgs = mysqli_fetch_assoc($res_imgs)) {
			$total_images = intval($row_imgs['img_count']);
		}
		$total_docs = max(0, $total_files - $total_images);

		// OCR counts
		$res_ocr = @mysqli_query($conn, "SELECT 
			SUM(CASE WHEN ocr_status = 'completed' THEN 1 ELSE 0 END) as done_count,
			SUM(CASE WHEN ocr_status != 'completed' THEN 1 ELSE 0 END) as pending_count
			FROM bill_export");
		if ($res_ocr && $row_ocr = mysqli_fetch_assoc($res_ocr)) {
			$total_ocr_done = intval($row_ocr['done_count'] ?? 0);
			$total_ocr_pending = intval($row_ocr['pending_count'] ?? 0);
		}

		// Calculate total parsed bill amounts
		$res_amt = @mysqli_query($conn, "SELECT total_amount FROM bill_export WHERE ocr_status = 'completed' AND total_amount IS NOT NULL");
		if ($res_amt) {
			while ($row_amt = mysqli_fetch_assoc($res_amt)) {
				$val = preg_replace('/[^0-9\.]/', '', $row_amt['total_amount']);
				if (is_numeric($val)) {
					$total_billed_amount += floatval($val);
				}
			}
		}

		$this->assign("rs_bills", $rs_bills);
		$this->assign("search_query", $search_query);
		$this->assign("file_category", $file_category);
		$this->assign("ocr_filter", $ocr_filter);
		$this->assign("total_files", $total_files);
		$this->assign("total_images", $total_images);
		$this->assign("total_docs", $total_docs);
		$this->assign("total_size", $total_size);
		$this->assign("total_ocr_done", $total_ocr_done);
		$this->assign("total_ocr_pending", $total_ocr_pending);
		$this->assign("total_billed_amount", $total_billed_amount);
	}

	/**
	 * Calls FastAPI OCR backend with the bill file.
	 */
	private function process_file_ocr($full_file_path, $original_name, $mime_type) {
		if (!file_exists($full_file_path)) {
			return array('success' => false, 'error' => 'File does not exist on disk.');
		}

		// Initialize cURL request to FastAPI OCR
		$ch = curl_init();
		curl_setopt($ch, CURLOPT_URL, $this->ocr_backend_url);
		curl_setopt($ch, CURLOPT_POST, true);
		curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
		curl_setopt($ch, CURLOPT_TIMEOUT, 35);
		curl_setopt($ch, CURLOPT_CONNECTTIMEOUT, 5);

		// Prefer CURLFile multipart upload
		if (function_exists('curl_file_create')) {
			$cfile = curl_file_create($full_file_path, $mime_type, $original_name);
			$post_data = array('file' => $cfile);
		} else {
			$post_data = array('file' => '@' . realpath($full_file_path));
		}

		curl_setopt($ch, CURLOPT_POSTFIELDS, $post_data);

		$response = curl_exec($ch);
		$http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
		$curl_err = curl_error($ch);
		curl_close($ch);

		if ($curl_err) {
			return array('success' => false, 'error' => "cURL Error: " . $curl_err);
		}

		$json = json_decode($response, true);
		if ($http_code == 200 && isset($json['status']) && $json['status'] == 'success') {
			return array('success' => true, 'data' => $json['data'] ?? array());
		}

		$err_msg = $json['message'] ?? ("HTTP " . $http_code . " from OCR backend");
		return array('success' => false, 'error' => $err_msg);
	}

	/**
	 * Upload Bill Files & Auto-trigger Backend OCR
	 */
	function upload_bill() {
		$conn = $this->app->objDB->getConnection();
		$this->ensure_table_schema($conn);

		if (!isset($_FILES['bill_files'])) {
			$this->app->utility->set_message("No files were selected for upload.", "ERROR");
			$this->app->redirect("index.php?view=bill_export_list");
			return;
		}

		$files = $_FILES['bill_files'];
		$file_list = array();

		if (is_array($files['name'])) {
			for ($i = 0; $i < count($files['name']); $i++) {
				if (!empty($files['name'][$i])) {
					$file_list[] = array(
						'name'     => $files['name'][$i],
						'type'     => $files['type'][$i],
						'tmp_name' => $files['tmp_name'][$i],
						'error'    => $files['error'][$i],
						'size'     => $files['size'][$i]
					);
				}
			}
		} else if (!empty($files['name'])) {
			$file_list[] = $files;
		}

		if (empty($file_list)) {
			$this->app->utility->set_message("Please select at least one valid bill file or image to upload.", "ERROR");
			$this->app->redirect("index.php?view=bill_export_list");
			return;
		}

		$upload_dir = ABS_PATH . DS . "uploads" . DS . "bill_export" . DS;
		if (!file_exists($upload_dir)) {
			@mkdir($upload_dir, 0755, true);
		}

		$user_id = isset($_SESSION['admin_user_id']) ? intval($_SESSION['admin_user_id']) : 1;
		$uploaded_count = 0;
		$ocr_success_count = 0;
		$errors = array();

		foreach ($file_list as $file) {
			if ($file['error'] !== UPLOAD_ERR_OK) {
				$errors[] = "Upload error for " . htmlspecialchars($file['name']);
				continue;
			}

			$original_name = $file['name'];
			$extension = strtolower(pathinfo($original_name, PATHINFO_EXTENSION));
			$mime_type = !empty($file['type']) ? $file['type'] : $extension;

			$safe_name = preg_replace('/[^a-zA-Z0-9_\.-]/', '_', pathinfo($original_name, PATHINFO_FILENAME));
			$stored_filename = "bill_" . time() . "_" . mt_rand(1000, 9999) . "_" . $safe_name . "." . $extension;
			$target_path = $upload_dir . $stored_filename;
			$relative_path = "uploads/bill_export/" . $stored_filename;

			if (move_uploaded_file($file['tmp_name'], $target_path)) {
				// 1. Insert Base Record
				$obj_model = $this->app->load_model("bill_export");
				$fields = array(
					'user_id'       => $user_id,
					'original_name' => $original_name,
					'file_path'     => $relative_path,
					'file_type'     => $mime_type,
					'file_size'     => $file['size'],
					'status'        => 'active',
					'ocr_status'    => 'processing'
				);
				$obj_model->map_fields($fields);
				$insert_id = $obj_model->execute("INSERT");

				if ($insert_id) {
					$uploaded_count++;

					// 2. Process Backend OCR Immediately
					$ocr_res = $this->process_file_ocr($target_path, $original_name, $mime_type);
					if ($ocr_res['success']) {
						$ocr_data = $ocr_res['data'];
						$ocr_status = 'completed';
						$ocr_success_count++;

						// Prepare sanitized DB update
						$v_name = mysqli_real_escape_string($conn, $ocr_data['vendor_name'] ?? '');
						$b_num  = mysqli_real_escape_string($conn, $ocr_data['bill_number'] ?? '');
						$b_date = mysqli_real_escape_string($conn, $ocr_data['bill_date'] ?? '');
						$d_date = mysqli_real_escape_string($conn, $ocr_data['due_date'] ?? '');
						$curr   = mysqli_real_escape_string($conn, $ocr_data['currency'] ?? 'INR');
						$subtot = mysqli_real_escape_string($conn, $ocr_data['subtotal'] ?? '');
						$taxamt = mysqli_real_escape_string($conn, $ocr_data['tax_amount'] ?? '');
						$totamt = mysqli_real_escape_string($conn, $ocr_data['total_amount'] ?? '');
						$payst  = mysqli_real_escape_string($conn, $ocr_data['payment_status'] ?? '');
						$summary= mysqli_real_escape_string($conn, $ocr_data['summary'] ?? '');
						$rawtext= mysqli_real_escape_string($conn, $ocr_data['raw_text'] ?? '');
						$jsonraw= mysqli_real_escape_string($conn, json_encode($ocr_data, JSON_UNESCAPED_UNICODE));

						$update_sql = "UPDATE bill_export SET 
							ocr_status = '$ocr_status',
							vendor_name = '$v_name',
							bill_number = '$b_num',
							bill_date = '$b_date',
							due_date = '$d_date',
							currency = '$curr',
							subtotal = '$subtot',
							tax_amount = '$taxamt',
							total_amount = '$totamt',
							payment_status = '$payst',
							ocr_summary = '$summary',
							ocr_data = '$jsonraw',
							ocr_text = '$rawtext'
							WHERE id = $insert_id";

						@mysqli_query($conn, $update_sql);
					} else {
						// Mark as failed or pending without breaking upload
						$err_clean = mysqli_real_escape_string($conn, $ocr_res['error'] ?? 'OCR Failed');
						@mysqli_query($conn, "UPDATE bill_export SET ocr_status = 'failed', ocr_summary = '$err_clean' WHERE id = $insert_id");
					}
				} else {
					$errors[] = "Database insert failed for " . htmlspecialchars($original_name);
				}
			} else {
				$errors[] = "Failed to save file " . htmlspecialchars($original_name) . " to directory.";
			}
		}

		if ($uploaded_count > 0) {
			$msg = "$uploaded_count bill(s) uploaded successfully! ($ocr_success_count processed with AI OCR).";
			if (!empty($errors)) {
				$msg .= " (Note: " . implode(", ", $errors) . ")";
			}
			$this->app->utility->set_message($msg, "SUCCESS");
		} else {
			$this->app->utility->set_message("Upload failed: " . implode(", ", $errors), "ERROR");
		}

		$this->app->redirect("index.php?view=bill_export_list");
	}

	/**
	 * Re-run OCR on an existing bill (Supports both normal and AJAX requests)
	 */
	function reprocess_ocr() {
		$bill_id = intval($this->app->getPostVar('id') ?? $this->app->getGetVar('id'));
		$is_ajax = (!empty($_SERVER['HTTP_X_REQUESTED_WITH']) && strtolower($_SERVER['HTTP_X_REQUESTED_WITH']) == 'xmlhttprequest') || isset($_GET['ajax']);

		if ($bill_id <= 0) {
			if ($is_ajax) {
				echo json_encode(array('status' => 'error', 'message' => 'Invalid bill ID.'));
				exit;
			}
			$this->app->utility->set_message("Invalid bill ID.", "ERROR");
			$this->app->redirect("index.php?view=bill_export_list");
			return;
		}

		$conn = $this->app->objDB->getConnection();
		$res = mysqli_query($conn, "SELECT * FROM bill_export WHERE id = $bill_id LIMIT 1");
		if (!$res || mysqli_num_rows($res) == 0) {
			if ($is_ajax) {
				echo json_encode(array('status' => 'error', 'message' => 'Bill not found.'));
				exit;
			}
			$this->app->utility->set_message("Bill not found.", "ERROR");
			$this->app->redirect("index.php?view=bill_export_list");
			return;
		}

		$bill = mysqli_fetch_assoc($res);
		$full_path = ABS_PATH . DS . str_replace('/', DS, $bill['file_path']);

		$ocr_res = $this->process_file_ocr($full_path, $bill['original_name'], $bill['file_type']);

		if ($ocr_res['success']) {
			$ocr_data = $ocr_res['data'];
			$v_name = mysqli_real_escape_string($conn, $ocr_data['vendor_name'] ?? '');
			$b_num  = mysqli_real_escape_string($conn, $ocr_data['bill_number'] ?? '');
			$b_date = mysqli_real_escape_string($conn, $ocr_data['bill_date'] ?? '');
			$d_date = mysqli_real_escape_string($conn, $ocr_data['due_date'] ?? '');
			$curr   = mysqli_real_escape_string($conn, $ocr_data['currency'] ?? 'INR');
			$subtot = mysqli_real_escape_string($conn, $ocr_data['subtotal'] ?? '');
			$taxamt = mysqli_real_escape_string($conn, $ocr_data['tax_amount'] ?? '');
			$totamt = mysqli_real_escape_string($conn, $ocr_data['total_amount'] ?? '');
			$payst  = mysqli_real_escape_string($conn, $ocr_data['payment_status'] ?? '');
			$summary= mysqli_real_escape_string($conn, $ocr_data['summary'] ?? '');
			$rawtext= mysqli_real_escape_string($conn, $ocr_data['raw_text'] ?? '');
			$jsonraw= mysqli_real_escape_string($conn, json_encode($ocr_data, JSON_UNESCAPED_UNICODE));

			$update_sql = "UPDATE bill_export SET 
				ocr_status = 'completed',
				vendor_name = '$v_name',
				bill_number = '$b_num',
				bill_date = '$b_date',
				due_date = '$d_date',
				currency = '$curr',
				subtotal = '$subtot',
				tax_amount = '$taxamt',
				total_amount = '$totamt',
				payment_status = '$payst',
				ocr_summary = '$summary',
				ocr_data = '$jsonraw',
				ocr_text = '$rawtext'
				WHERE id = $bill_id";

			mysqli_query($conn, $update_sql);

			if ($is_ajax) {
				echo json_encode(array('status' => 'success', 'message' => 'OCR completed successfully!', 'data' => $ocr_data));
				exit;
			}
			$this->app->utility->set_message("OCR reprocessed successfully for '" . htmlspecialchars($bill['original_name']) . "'!", "SUCCESS");
		} else {
			$err_msg = $ocr_res['error'] ?? 'OCR Extraction Failed';
			$err_clean = mysqli_real_escape_string($conn, $err_msg);
			mysqli_query($conn, "UPDATE bill_export SET ocr_status = 'failed', ocr_summary = '$err_clean' WHERE id = $bill_id");

			if ($is_ajax) {
				echo json_encode(array('status' => 'error', 'message' => $err_msg));
				exit;
			}
			$this->app->utility->set_message("OCR failed: " . htmlspecialchars($err_msg), "ERROR");
		}

		$this->app->redirect("index.php?view=bill_export_list");
	}

	/**
	 * Returns JSON details of OCR for the modal view
	 */
	function get_ocr_details() {
		$bill_id = intval($this->app->getPostVar('id') ?? $this->app->getGetVar('id'));
		header('Content-Type: application/json');

		if ($bill_id <= 0) {
			echo json_encode(array('status' => 'error', 'message' => 'Invalid bill ID'));
			exit;
		}

		$conn = $this->app->objDB->getConnection();
		$res = mysqli_query($conn, "SELECT * FROM bill_export WHERE id = $bill_id LIMIT 1");
		if ($res && $bill = mysqli_fetch_assoc($res)) {
			$parsed_json = !empty($bill['ocr_data']) ? json_decode($bill['ocr_data'], true) : null;
			echo json_encode(array(
				'status' => 'success',
				'bill' => array(
					'id'            => $bill['id'],
					'original_name' => $bill['original_name'],
					'file_path'     => $bill['file_path'],
					'file_type'     => $bill['file_type'],
					'ocr_status'    => $bill['ocr_status'],
					'vendor_name'   => $bill['vendor_name'],
					'bill_number'   => $bill['bill_number'],
					'bill_date'     => $bill['bill_date'],
					'due_date'      => $bill['due_date'],
					'currency'      => $bill['currency'] ?: 'INR',
					'subtotal'      => $bill['subtotal'],
					'tax_amount'    => $bill['tax_amount'],
					'total_amount'  => $bill['total_amount'],
					'payment_status'=> $bill['payment_status'],
					'ocr_summary'   => $bill['ocr_summary'],
					'ocr_text'      => $bill['ocr_text'],
					'ocr_data'      => $parsed_json,
					'created_at'    => $bill['created_at']
				)
			));
			exit;
		}

		echo json_encode(array('status' => 'error', 'message' => 'Bill not found.'));
		exit;
	}

	/**
	 * Delete bill file and database record
	 */
	function delete_bill() {
		$file_id = intval($this->app->getPostVar('id') ?? $this->app->getGetVar('id'));
		if ($file_id > 0) {
			$conn = $this->app->objDB->getConnection();
			$res = mysqli_query($conn, "SELECT file_path, original_name FROM bill_export WHERE id = $file_id LIMIT 1");
			if ($res && $row = mysqli_fetch_assoc($res)) {
				$full_path = ABS_PATH . DS . str_replace('/', DS, $row['file_path']);
				if (file_exists($full_path)) {
					@unlink($full_path);
				}
				mysqli_query($conn, "DELETE FROM bill_export WHERE id = $file_id");
				$this->app->utility->set_message("Bill file '" . htmlspecialchars($row['original_name']) . "' deleted successfully.", "SUCCESS");
			} else {
				$this->app->utility->set_message("Bill file not found or already deleted.", "ERROR");
			}
		}
		$this->app->redirect("index.php?view=bill_export_list");
	}
}
?>
