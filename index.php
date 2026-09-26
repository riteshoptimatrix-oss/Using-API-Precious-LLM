<?php include("includes/header.php"); ?>

<?php
function format_bytes_view($bytes, $precision = 2) {
    $units = array('B', 'KB', 'MB', 'GB', 'TB');
    $bytes = max($bytes, 0);
    $pow = floor(($bytes ? log($bytes) : 0) / log(1024));
    $pow = min($pow, count($units) - 1);
    $bytes /= pow(1024, $pow);
    return round($bytes, $precision) . ' ' . $units[$pow];
}
?>

<div class="content pt-3">
  <div class="container-fluid">

    <!-- Page Header & Action Bar -->
    <div class="card card-primary card-outline mb-3 shadow-sm">
      <div class="card-header bg-white">
        <div class="row align-items-center">
          <div class="col-md-6 col-12 mb-2 mb-md-0">
            <h1 class="h4 mb-0 text-dark font-weight-bold">
              <i class="fas fa-file-invoice-dollar text-primary mr-2"></i> Bill Export & AI OCR Management
            </h1>
            <small class="text-muted">Automated Invoice, Receipt & Bill OCR Extraction powered by Gemini AI</small>
          </div>
          <div class="col-md-6 col-12 text-md-right">
            <button type="button" class="btn btn-primary btn-sm mr-1 shadow-sm" onclick="$('#uploadCollapse').collapse('toggle')">
              <i class="fas fa-cloud-upload-alt mr-1"></i> Upload Bills
            </button>
            <button type="button" class="btn btn-secondary btn-sm shadow-sm" onclick="javascript:location.reload(true)">
              <i class="fas fa-sync mr-1"></i> Refresh
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Summary Metrics Row -->
    <div class="row mb-3">
      <!-- Total Bills -->
      <div class="col-xl-3 col-md-6 col-12 mb-2">
        <div class="small-box bg-info shadow-sm rounded">
          <div class="inner p-3">
            <h3><?php echo number_format($this->total_files ?? 0); ?></h3>
            <p class="mb-0 font-weight-bold">Total Uploaded Bills</p>
            <small class="text-white-50"><?php echo format_bytes_view($this->total_size ?? 0); ?> storage used</small>
          </div>
          <div class="icon">
            <i class="fas fa-file-invoice"></i>
          </div>
        </div>
      </div>

      <!-- OCR Processed -->
      <div class="col-xl-3 col-md-6 col-12 mb-2">
        <div class="small-box bg-success shadow-sm rounded">
          <div class="inner p-3">
            <h3><?php echo number_format($this->total_ocr_done ?? 0); ?></h3>
            <p class="mb-0 font-weight-bold">OCR Processed</p>
            <small class="text-white-50">Extracted by Gemini AI</small>
          </div>
          <div class="icon">
            <i class="fas fa-check-circle"></i>
          </div>
        </div>
      </div>

      <!-- Total Billed Amount -->
      <div class="col-xl-3 col-md-6 col-12 mb-2">
        <div class="small-box bg-primary shadow-sm rounded">
          <div class="inner p-3">
            <h3>₹ <?php echo number_format($this->total_billed_amount ?? 0, 2); ?></h3>
            <p class="mb-0 font-weight-bold">Total Bill Value</p>
            <small class="text-white-50">Calculated from parsed bills</small>
          </div>
          <div class="icon">
            <i class="fas fa-coins"></i>
          </div>
        </div>
      </div>

      <!-- OCR Pending / Failed -->
      <div class="col-xl-3 col-md-6 col-12 mb-2">
        <div class="small-box bg-warning shadow-sm rounded">
          <div class="inner p-3">
            <h3><?php echo number_format($this->total_ocr_pending ?? 0); ?></h3>
            <p class="mb-0 font-weight-bold text-dark">OCR Pending / Review</p>
            <small class="text-dark">Ready for reprocessing</small>
          </div>
          <div class="icon">
            <i class="fas fa-hourglass-half"></i>
          </div>
        </div>
      </div>
    </div>

    <!-- Upload Section Card -->
    <div class="collapse show mb-3" id="uploadCollapse">
      <div class="card card-primary card-outline shadow-sm">
        <div class="card-header bg-light py-2">
          <h3 class="card-title font-weight-bold mb-0">
            <i class="fas fa-cloud-upload-alt text-primary mr-2"></i> Upload New Bill Files & Images (Auto AI OCR)
          </h3>
        </div>
        <div class="card-body">
          <form action="index.php?view=bill_export_list" method="POST" enctype="multipart/form-data" id="frm_upload_bill">
            <input type="hidden" name="act" value="upload_bill">

            <div class="upload-drop-zone p-4 text-center border rounded mb-3 bg-light" id="drop_zone" style="border: 2px dashed #007bff !important; transition: all 0.3s ease;">
              <i class="fas fa-file-upload fa-3x text-primary mb-2"></i>
              <h5 class="font-weight-bold text-dark">Drag and drop bill files or images here</h5>
              <p class="text-muted small mb-3">Supports Invoices & Bills in Image format (JPG, PNG, WEBP) and PDF Documents</p>
              
              <div class="d-inline-block">
                <label for="bill_files" class="btn btn-primary btn-md px-4 py-2 cursor-pointer mb-0 shadow-sm font-weight-bold">
                  <i class="fas fa-folder-open mr-2"></i> Choose Bill Files...
                </label>
                <input type="file" name="bill_files[]" id="bill_files" class="d-none" multiple required onchange="handleFileSelect(this)">
              </div>
            </div>

            <!-- Selected Files Preview Container -->
            <div id="file_preview_list" class="mb-3 d-none">
              <label class="font-weight-bold small text-muted">Selected File(s) to Upload & Process:</label>
              <div class="d-flex flex-wrap gap-2" id="selected_files_badges"></div>
            </div>

            <div class="row align-items-center">
              <div class="col-md-8 text-muted small">
                <i class="fas fa-magic text-primary mr-1"></i> <strong>AI Multimodal OCR Active:</strong> Each uploaded file is automatically processed by Gemini Vision to extract Vendor Name, Bill Number, Amounts, Taxes, and Line Items.
              </div>
              <div class="col-md-4 text-right mt-2 mt-md-0">
                <button type="submit" class="btn btn-danger btn-block font-weight-bold shadow-sm" id="btn_upload_submit">
                  <i class="fas fa-upload mr-1"></i> Upload & Process OCR Now
                </button>
              </div>
            </div>

          </form>
        </div>
      </div>
    </div>

    <!-- Filter & Search Section -->
    <div class="card card-outline card-secondary mb-3 shadow-sm">
      <div class="card-header py-2 bg-light">
        <form action="index.php?view=bill_export_list" method="POST" class="form-inline" id="frm_search_bill">
          <div class="form-group mr-3 mb-2 mb-md-0">
            <label for="search_query" class="small font-weight-bold mr-2">Search:</label>
            <input type="text" name="search_query" id="search_query" class="form-control form-control-sm" placeholder="Vendor, Bill #, or File name..." value="<?php echo htmlspecialchars($this->search_query ?? ''); ?>" style="min-width: 240px;">
          </div>

          <div class="form-group mr-3 mb-2 mb-md-0">
            <label for="ocr_filter" class="small font-weight-bold mr-2">OCR Status:</label>
            <select name="ocr_filter" id="ocr_filter" class="form-control form-control-sm" style="min-width: 150px;">
              <option value="">All Statuses</option>
              <option value="completed" <?php echo (isset($this->ocr_filter) && $this->ocr_filter == 'completed' ? 'selected' : ''); ?>>OCR Completed</option>
              <option value="processing" <?php echo (isset($this->ocr_filter) && $this->ocr_filter == 'processing' ? 'selected' : ''); ?>>Processing</option>
              <option value="pending" <?php echo (isset($this->ocr_filter) && $this->ocr_filter == 'pending' ? 'selected' : ''); ?>>Pending</option>
              <option value="failed" <?php echo (isset($this->ocr_filter) && $this->ocr_filter == 'failed' ? 'selected' : ''); ?>>Failed</option>
            </select>
          </div>

          <div class="form-group mr-3 mb-2 mb-md-0">
            <label for="file_category" class="small font-weight-bold mr-2">File Type:</label>
            <select name="file_category" id="file_category" class="form-control form-control-sm" style="min-width: 140px;">
              <option value="">All Files</option>
              <option value="image" <?php echo (isset($this->file_category) && $this->file_category == 'image' ? 'selected' : ''); ?>>Images Only</option>
              <option value="document" <?php echo (isset($this->file_category) && $this->file_category == 'document' ? 'selected' : ''); ?>>PDF & Docs Only</option>
            </select>
          </div>

          <button type="submit" class="btn btn-primary btn-sm mr-2 mb-2 mb-md-0 shadow-sm">
            <i class="fas fa-search mr-1"></i> Filter
          </button>
          <a href="index.php?view=bill_export_list" class="btn btn-secondary btn-sm mb-2 mb-md-0">
            <i class="fas fa-undo mr-1"></i> Reset
          </a>
        </form>
      </div>
    </div>

    <!-- Bills Listing Table Card -->
    <div class="card shadow-sm">
      <div class="card-header bg-white border-bottom py-2">
        <h3 class="card-title font-weight-bold mb-0">
          <i class="fas fa-list text-primary mr-2"></i> Uploaded Bills with AI OCR Extracted Information
        </h3>
      </div>
      <div class="card-body p-0 table-responsive">
        <?php echo $this->utility->get_message(); ?>

        <table class="table table-hover table-bordered table-striped align-middle mb-0" id="tbl_bills">
          <thead class="thead-light">
            <tr>
              <th style="width: 50px;" class="text-center">ID</th>
              <th style="width: 80px;" class="text-center">Preview</th>
              <th>Bill & Vendor Info</th>
              <th style="width: 150px;">Bill # & Date</th>
              <th style="width: 140px;" class="text-right">Total Amount</th>
              <th style="width: 120px;" class="text-center">OCR Status</th>
              <th style="width: 140px;">Uploaded By</th>
              <th style="width: 180px;" class="text-center">Actions</th>
            </tr>
          </thead>
          <tbody>
            <?php
            if (isset($this->rs_bills) && count($this->rs_bills) > 0) {
              foreach ($this->rs_bills as $bill) {
                $ext = strtolower(pathinfo($bill['original_name'], PATHINFO_EXTENSION));
                $mime = strtolower($bill['file_type']);
                $is_image = (strpos($mime, 'image/') !== false || in_array($ext, array('jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp', 'svg')));
                $file_url = "../" . $bill['file_path'];
                $formatted_size = format_bytes_view($bill['file_size']);
                $ocr_status = strtolower($bill['ocr_status'] ?? 'pending');
            ?>
              <tr id="row_bill_<?php echo $bill['id']; ?>">
                <!-- ID -->
                <td class="text-center font-weight-bold align-middle"><?php echo htmlspecialchars($bill['id']); ?></td>

                <!-- Thumbnail / Preview -->
                <td class="text-center align-middle">
                  <?php if ($is_image) { ?>
                    <img src="<?php echo htmlspecialchars($file_url); ?>" alt="Bill Image" class="img-thumbnail rounded cursor-pointer bill-thumb" style="width: 50px; height: 50px; object-fit: cover; border: 1px solid #dee2e6;" onclick="openImageModal('<?php echo htmlspecialchars($file_url); ?>', '<?php echo htmlspecialchars(addslashes($bill['original_name'])); ?>')">
                  <?php } elseif (in_array($ext, array('pdf'))) { ?>
                    <span class="badge badge-light p-2 border"><i class="fas fa-file-pdf fa-2x text-danger"></i></span>
                  <?php } else { ?>
                    <span class="badge badge-light p-2 border"><i class="fas fa-file-alt fa-2x text-secondary"></i></span>
                  <?php } ?>
                </td>

                <!-- Bill & Vendor Info -->
                <td class="align-middle">
                  <?php if (!empty($bill['vendor_name'])) { ?>
                    <div class="font-weight-bold text-dark">
                      <i class="fas fa-store text-primary mr-1"></i> <?php echo htmlspecialchars($bill['vendor_name']); ?>
                    </div>
                  <?php } ?>
                  <div>
                    <a href="<?php echo htmlspecialchars($file_url); ?>" target="_blank" class="text-primary text-decoration-none small font-weight-bold">
                      <i class="fas fa-paperclip mr-1"></i> <?php echo htmlspecialchars($bill['original_name']); ?>
                    </a>
                  </div>
                  <div class="small text-muted">
                    <span class="badge badge-secondary uppercase px-1"><?php echo strtoupper($ext); ?></span>
                    <span class="ml-1"><?php echo $formatted_size; ?></span>
                  </div>
                </td>

                <!-- Bill # & Date -->
                <td class="align-middle small">
                  <?php if (!empty($bill['bill_number'])) { ?>
                    <div class="font-weight-bold text-dark">
                      <i class="fas fa-hashtag text-muted mr-1"></i><?php echo htmlspecialchars($bill['bill_number']); ?>
                    </div>
                  <?php } else { ?>
                    <span class="text-muted font-italic">No Bill #</span>
                  <?php } ?>

                  <?php if (!empty($bill['bill_date'])) { ?>
                    <div class="text-muted">
                      <i class="far fa-calendar-alt text-secondary mr-1"></i><?php echo htmlspecialchars($bill['bill_date']); ?>
                    </div>
                  <?php } ?>
                </td>

                <!-- Total Amount -->
                <td class="align-middle text-right">
                  <?php if (!empty($bill['total_amount'])) { ?>
                    <div class="font-weight-bold text-success h6 mb-0">
                      <?php echo htmlspecialchars($bill['currency'] ?: '₹'); ?> <?php echo htmlspecialchars($bill['total_amount']); ?>
                    </div>
                    <?php if (!empty($bill['tax_amount'])) { ?>
                      <small class="text-muted d-block">Tax: <?php echo htmlspecialchars($bill['tax_amount']); ?></small>
                    <?php } ?>
                  <?php } else { ?>
                    <span class="text-muted font-italic small">-</span>
                  <?php } ?>
                </td>

                <!-- OCR Status -->
                <td class="text-center align-middle">
                  <?php if ($ocr_status == 'completed') { ?>
                    <span class="badge badge-success px-2 py-1"><i class="fas fa-check-circle mr-1"></i> Done</span>
                  <?php } elseif ($ocr_status == 'processing') { ?>
                    <span class="badge badge-info px-2 py-1"><i class="fas fa-spinner fa-spin mr-1"></i> Processing</span>
                  <?php } elseif ($ocr_status == 'failed') { ?>
                    <span class="badge badge-danger px-2 py-1" title="<?php echo htmlspecialchars($bill['ocr_summary'] ?? 'OCR Failed'); ?>"><i class="fas fa-exclamation-circle mr-1"></i> Failed</span>
                  <?php } else { ?>
                    <span class="badge badge-secondary px-2 py-1"><i class="fas fa-clock mr-1"></i> Pending</span>
                  <?php } ?>
                </td>

                <!-- Uploaded By & Date -->
                <td class="align-middle small">
                  <div class="font-weight-bold text-dark">
                    <i class="fas fa-user-circle text-secondary mr-1"></i> <?php echo htmlspecialchars($bill['uploaded_by_name'] ?? 'Admin User'); ?>
                  </div>
                  <div class="text-muted">
                    <i class="far fa-clock mr-1"></i> <?php echo date('d-m-Y h:i A', strtotime($bill['created_at'])); ?>
                  </div>
                </td>

                <!-- Actions -->
                <td class="text-center align-middle">
                  <!-- View OCR Details Button -->
                  <button type="button" class="btn btn-sm btn-primary mr-1 shadow-sm" title="View Extracted OCR Data" onclick="viewOcrModal(<?php echo $bill['id']; ?>)">
                    <i class="fas fa-file-invoice"></i> OCR
                  </button>

                  <!-- Preview / View File -->
                  <?php if ($is_image) { ?>
                    <button type="button" class="btn btn-sm btn-info mr-1 shadow-sm" title="Preview Image" onclick="openImageModal('<?php echo htmlspecialchars($file_url); ?>', '<?php echo htmlspecialchars(addslashes($bill['original_name'])); ?>')">
                      <i class="fas fa-eye"></i>
                    </button>
                  <?php } else { ?>
                    <a href="<?php echo htmlspecialchars($file_url); ?>" target="_blank" class="btn btn-sm btn-info mr-1 shadow-sm" title="View Document">
                      <i class="fas fa-external-link-alt"></i>
                    </a>
                  <?php } ?>

                  <!-- Reprocess OCR Button -->
                  <button type="button" class="btn btn-sm btn-warning mr-1 shadow-sm btn-reprocess-ocr" title="Re-run AI OCR" onclick="reprocessOcr(<?php echo $bill['id']; ?>, this)">
                    <i class="fas fa-sync"></i>
                  </button>

                  <!-- Delete -->
                  <button type="button" class="btn btn-sm btn-danger shadow-sm" title="Delete File" onclick="confirmDeleteBill(<?php echo $bill['id']; ?>, '<?php echo htmlspecialchars(addslashes($bill['original_name'])); ?>')">
                    <i class="fas fa-trash-alt"></i>
                  </button>
                </td>
              </tr>
            <?php
              }
            } else {
            ?>
              <tr>
                <td colspan="8" class="text-center text-muted py-5">
                  <i class="fas fa-folder-open fa-3x text-muted mb-3 d-block"></i>
                  <h5 class="font-weight-bold">No Bill Files Uploaded Yet</h5>
                  <p class="small text-muted">Upload bill images or PDFs above. AI will automatically extract financial data!</p>
                </td>
              </tr>
            <?php
            }
            ?>
          </tbody>
        </table>
      </div>

      <!-- Card Footer Pagination -->
      <div class="card-footer bg-white border-top py-3">
        <?php echo $this->objDB->show_paging("rs_bills"); ?>
      </div>
    </div>

  </div>
</div>

<!-- ===================================================================== -->
<!-- OCR Details Inspection Modal -->
<!-- ===================================================================== -->
<div class="modal fade" id="ocrDetailsModal" tabindex="-1" role="dialog" aria-labelledby="ocrDetailsModalLabel" aria-hidden="true">
  <div class="modal-dialog modal-xl modal-dialog-centered" role="document">
    <div class="modal-content shadow-lg border-0">
      
      <div class="modal-header bg-primary text-white py-3">
        <h5 class="modal-title font-weight-bold" id="ocrDetailsModalLabel">
          <i class="fas fa-file-invoice-dollar mr-2"></i> AI OCR Extracted Bill Information
        </h5>
        <button type="button" class="close text-white" data-dismiss="modal" aria-label="Close">
          <span aria-hidden="true">&times;</span>
        </button>
      </div>

      <div class="modal-body p-4 bg-light" id="ocrModalBody">
        <!-- Dynamic loading spinner -->
        <div class="text-center py-5" id="ocrModalLoading">
          <i class="fas fa-spinner fa-spin fa-3x text-primary mb-3"></i>
          <h5 class="font-weight-bold">Fetching OCR Data...</h5>
          <p class="text-muted small">Please wait while details are loaded.</p>
        </div>

        <!-- Dynamic details content -->
        <div id="ocrModalContent" class="d-none">

          <!-- Top Summary Alert -->
          <div class="alert alert-info border-left shadow-sm py-2 px-3 mb-3" style="border-left: 4px solid #17a2b8 !important;">
            <i class="fas fa-info-circle mr-1 font-weight-bold"></i> <strong>AI Summary:</strong> <span id="ocr_summary_text">-</span>
          </div>

          <div class="row">
            <!-- Left Column: Primary Extracted Fields -->
            <div class="col-md-6 mb-3">
              <div class="card h-100 shadow-sm border-0">
                <div class="card-header bg-white font-weight-bold text-dark border-bottom py-2">
                  <i class="fas fa-receipt text-primary mr-1"></i> Bill & Merchant Details
                </div>
                <div class="card-body p-3">
                  <table class="table table-sm table-borderless mb-0">
                    <tr>
                      <th class="text-muted" style="width: 140px;">Vendor / Seller:</th>
                      <td class="font-weight-bold text-dark" id="ocr_vendor_name">-</td>
                    </tr>
                    <tr>
                      <th class="text-muted">Bill / Invoice #:</th>
                      <td class="font-weight-bold" id="ocr_bill_number">-</td>
                    </tr>
                    <tr>
                      <th class="text-muted">Bill Date:</th>
                      <td id="ocr_bill_date">-</td>
                    </tr>
                    <tr>
                      <th class="text-muted">Due Date:</th>
                      <td id="ocr_due_date">-</td>
                    </tr>
                    <tr>
                      <th class="text-muted">Payment Status:</th>
                      <td id="ocr_payment_status">-</td>
                    </tr>
                    <tr>
                      <th class="text-muted">Original File:</th>
                      <td><a href="" id="ocr_file_link" target="_blank" class="text-primary font-weight-bold">-</a></td>
                    </tr>
                  </table>
                </div>
              </div>
            </div>

            <!-- Right Column: Financial Figures -->
            <div class="col-md-6 mb-3">
              <div class="card h-100 shadow-sm border-0">
                <div class="card-header bg-white font-weight-bold text-dark border-bottom py-2">
                  <i class="fas fa-money-bill-wave text-success mr-1"></i> Financial Summary
                </div>
                <div class="card-body p-3">
                  <table class="table table-sm table-borderless mb-0">
                    <tr>
                      <th class="text-muted" style="width: 140px;">Subtotal:</th>
                      <td class="font-weight-bold" id="ocr_subtotal">-</td>
                    </tr>
                    <tr>
                      <th class="text-muted">Tax / GST:</th>
                      <td class="font-weight-bold text-warning" id="ocr_tax_amount">-</td>
                    </tr>
                    <tr>
                      <th class="text-muted h5 mb-0">Grand Total:</th>
                      <td class="h4 font-weight-bold text-success mb-0" id="ocr_total_amount">-</td>
                    </tr>
                    <tr>
                      <th class="text-muted">Currency:</th>
                      <td class="badge badge-light border px-2 py-1 mt-1" id="ocr_currency">INR</td>
                    </tr>
                    <tr>
                      <th class="text-muted">OCR Status:</th>
                      <td id="ocr_status_badge">-</td>
                    </tr>
                  </table>
                </div>
              </div>
            </div>
          </div>

          <!-- Line Items Table -->
          <div class="card mb-3 shadow-sm border-0">
            <div class="card-header bg-white font-weight-bold text-dark border-bottom py-2">
              <i class="fas fa-list-ol text-primary mr-1"></i> Line Items / Products Breakdown
            </div>
            <div class="card-body p-0 table-responsive">
              <table class="table table-sm table-hover table-bordered mb-0">
                <thead class="thead-light">
                  <tr>
                    <th style="width: 40px;" class="text-center">#</th>
                    <th>Item Description</th>
                    <th style="width: 100px;" class="text-center">Qty</th>
                    <th style="width: 130px;" class="text-right">Unit Price</th>
                    <th style="width: 140px;" class="text-right">Amount</th>
                  </tr>
                </thead>
                <tbody id="ocr_items_tbody">
                  <tr><td colspan="5" class="text-center text-muted py-3">No line items detected</td></tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- Raw OCR Text & JSON Accordion -->
          <div class="accordion" id="ocrRawAccordion">
            <div class="card shadow-sm border-0 mb-2">
              <div class="card-header bg-white p-2" id="headingText">
                <button class="btn btn-link btn-block text-left text-dark font-weight-bold p-0 collapsed" type="button" data-toggle="collapse" data-target="#collapseText" aria-expanded="false" aria-controls="collapseText">
                  <i class="fas fa-align-left text-secondary mr-2"></i> Raw Transcribed Document Text <i class="fas fa-chevron-down float-right mt-1"></i>
                </button>
              </div>
              <div id="collapseText" class="collapse" aria-labelledby="headingText" data-parent="#ocrRawAccordion">
                <div class="card-body p-3 bg-light">
                  <pre id="ocr_raw_text" class="p-3 bg-white border rounded" style="max-height: 250px; overflow-y: auto; white-space: pre-wrap; font-size: 13px;"></pre>
                </div>
              </div>
            </div>
          </div>

        </div>
      </div>

      <div class="modal-footer py-2 bg-white">
        <button type="button" class="btn btn-warning btn-sm" id="btn_modal_reprocess">
          <i class="fas fa-sync mr-1"></i> Re-run AI OCR
        </button>
        <button type="button" class="btn btn-secondary btn-sm" data-dismiss="modal">Close</button>
      </div>

    </div>
  </div>
</div>

<!-- Image Preview Modal -->
<div class="modal fade" id="imagePreviewModal" tabindex="-1" role="dialog" aria-labelledby="imagePreviewModalLabel" aria-hidden="true">
  <div class="modal-dialog modal-lg modal-dialog-centered" role="document">
    <div class="modal-content">
      <div class="modal-header bg-primary text-white py-2">
        <h5 class="modal-title font-weight-bold" id="imagePreviewModalLabel">
          <i class="fas fa-image mr-2"></i> <span id="modal_image_title">Bill Image Preview</span>
        </h5>
        <button type="button" class="close text-white" data-dismiss="modal" aria-label="Close">
          <span aria-hidden="true">&times;</span>
        </button>
      </div>
      <div class="modal-body text-center p-3 bg-light">
        <img src="" id="modal_image_src" class="img-fluid rounded shadow-sm" style="max-height: 75vh; object-fit: contain;">
      </div>
      <div class="modal-footer py-2 bg-white">
        <a href="" id="modal_download_btn" download class="btn btn-primary btn-sm">
          <i class="fas fa-download mr-1"></i> Download Original Image
        </a>
        <button type="button" class="btn btn-secondary btn-sm" data-dismiss="modal">Close</button>
      </div>
    </div>
  </div>
</div>

<!-- Delete Bill Form -->
<form id="frm_delete_bill" action="index.php?view=bill_export_list" method="POST" style="display:none;">
  <input type="hidden" name="act" value="delete_bill">
  <input type="hidden" name="id" id="delete_bill_id">
</form>

<style>
.upload-drop-zone:hover {
  background-color: #e9ecef !important;
  border-color: #0056b3 !important;
}
.cursor-pointer {
  cursor: pointer;
}
.bill-thumb:hover {
  transform: scale(1.08);
  transition: transform 0.2s ease-in-out;
}
.gap-2 {
  gap: 0.5rem;
}
</style>

<script>
var currentActiveBillId = 0;

function handleFileSelect(input) {
  var container = $('#selected_files_badges');
  container.empty();
  
  if (input.files && input.files.length > 0) {
    $('#file_preview_list').removeClass('d-none');
    for (var i = 0; i < input.files.length; i++) {
      var f = input.files[i];
      var sizeKb = (f.size / 1024).toFixed(1) + ' KB';
      var badge = $('<span class="badge badge-info p-2 mr-1 mb-1 font-weight-normal"><i class="fas fa-file mr-1"></i> ' + f.name + ' (' + sizeKb + ')</span>');
      container.append(badge);
    }
  } else {
    $('#file_preview_list').addClass('d-none');
  }
}

function openImageModal(imgSrc, title) {
  $('#modal_image_src').attr('src', imgSrc);
  $('#modal_image_title').text(title);
  $('#modal_download_btn').attr('href', imgSrc).attr('download', title);
  $('#imagePreviewModal').modal('show');
}

function confirmDeleteBill(id, filename) {
  if (confirm("Are you sure you want to delete the bill file '" + filename + "'? This action cannot be undone.")) {
    $('#delete_bill_id').val(id);
    $('#frm_delete_bill').submit();
  }
}

function viewOcrModal(billId) {
  currentActiveBillId = billId;
  $('#ocrModalLoading').removeClass('d-none');
  $('#ocrModalContent').addClass('d-none');
  $('#ocrDetailsModal').modal('show');

  // Fetch OCR Details via AJAX
  $.ajax({
    url: 'index.php?view=bill_export_list&act=get_ocr_details&id=' + billId,
    type: 'GET',
    dataType: 'json',
    success: function(resp) {
      $('#ocrModalLoading').addClass('d-none');
      if (resp.status === 'success' && resp.bill) {
        var b = resp.bill;
        $('#ocrModalContent').removeClass('d-none');

        // Populate fields
        $('#ocr_summary_text').text(b.ocr_summary || 'Document extracted successfully.');
        $('#ocr_vendor_name').text(b.vendor_name || 'Not detected');
        $('#ocr_bill_number').text(b.bill_number || 'Not detected');
        $('#ocr_bill_date').text(b.bill_date || '-');
        $('#ocr_due_date').text(b.due_date || '-');
        $('#ocr_payment_status').text(b.payment_status || 'Unknown');
        
        var cur = b.currency || 'INR';
        $('#ocr_currency').text(cur);
        $('#ocr_subtotal').text(b.subtotal ? (cur + ' ' + b.subtotal) : '-');
        $('#ocr_tax_amount').text(b.tax_amount ? (cur + ' ' + b.tax_amount) : '-');
        $('#ocr_total_amount').text(b.total_amount ? (cur + ' ' + b.total_amount) : 'Not detected');

        $('#ocr_file_link').attr('href', '../' + b.file_path).text(b.original_name);

        var stBadge = '<span class="badge badge-secondary">Pending</span>';
        if (b.ocr_status === 'completed') {
          stBadge = '<span class="badge badge-success px-2 py-1"><i class="fas fa-check-circle mr-1"></i> Completed</span>';
        } else if (b.ocr_status === 'failed') {
          stBadge = '<span class="badge badge-danger px-2 py-1"><i class="fas fa-times-circle mr-1"></i> Failed</span>';
        }
        $('#ocr_status_badge').html(stBadge);

        // Populate Line Items Table
        var itemsTbody = $('#ocr_items_tbody');
        itemsTbody.empty();
        if (b.ocr_data && b.ocr_data.items && b.ocr_data.items.length > 0) {
          $.each(b.ocr_data.items, function(idx, item) {
            var row = $('<tr>' +
              '<td class="text-center font-weight-bold">' + (idx + 1) + '</td>' +
              '<td>' + (item.description || '-') + '</td>' +
              '<td class="text-center">' + (item.quantity || '1') + '</td>' +
              '<td class="text-right">' + (item.unit_price ? (cur + ' ' + item.unit_price) : '-') + '</td>' +
              '<td class="text-right font-weight-bold text-dark">' + (item.amount ? (cur + ' ' + item.amount) : '-') + '</td>' +
              '</tr>');
            itemsTbody.append(row);
          });
        } else {
          itemsTbody.append('<tr><td colspan="5" class="text-center text-muted py-3">No line items breakdown detected in this bill.</td></tr>');
        }

        // Raw Text
        $('#ocr_raw_text').text(b.ocr_text || 'No raw text available.');

      } else {
        alert(resp.message || 'Error loading OCR data.');
        $('#ocrDetailsModal').modal('hide');
      }
    },
    error: function() {
      $('#ocrModalLoading').addClass('d-none');
      alert('Network error while loading OCR data.');
    }
  });
}

function reprocessOcr(billId, btnEl) {
  var $btn = $(btnEl);
  var originalHtml = $btn.html();
  $btn.prop('disabled', true).html('<i class="fas fa-spinner fa-spin"></i>');

  $.ajax({
    url: 'index.php?view=bill_export_list&act=reprocess_ocr&ajax=1&id=' + billId,
    type: 'GET',
    dataType: 'json',
    success: function(resp) {
      $btn.prop('disabled', false).html(originalHtml);
      if (resp.status === 'success') {
        alert('AI OCR completed successfully!');
        location.reload();
      } else {
        alert('OCR failed: ' + (resp.message || 'Unknown error'));
      }
    },
    error: function() {
      $btn.prop('disabled', false).html(originalHtml);
      alert('Network error contacting server for OCR reprocessing.');
    }
  });
}

$('#btn_modal_reprocess').on('click', function() {
  if (currentActiveBillId > 0) {
    reprocessOcr(currentActiveBillId, this);
  }
});

$(document).ready(function() {
  // Drag and drop events for drop zone
  var dropZone = document.getElementById('drop_zone');
  var fileInput = document.getElementById('bill_files');

  if (dropZone && fileInput) {
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
      dropZone.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
      e.preventDefault();
      e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
      dropZone.addEventListener(eventName, () => {
        dropZone.style.backgroundColor = '#d0e2ff';
      }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
      dropZone.addEventListener(eventName, () => {
        dropZone.style.backgroundColor = '#f8f9fa';
      }, false);
    });

    dropZone.addEventListener('drop', (e) => {
      var dt = e.dataTransfer;
      var files = dt.files;
      if (files && files.length > 0) {
        fileInput.files = files;
        handleFileSelect(fileInput);
      }
    }, false);
  }
});
</script>

<?php include("includes/footer.php"); ?>
