# NowPayments API Update Documentation

## Problem Description

The NowPayments API has changed its response format. The old format used `payment_id` field, but the new format uses `id` field instead. This caused payment creation to fail with the error:

```
Invalid response from payment service. Missing payment_id or invoice_url.
```

## Root Cause

The API response now contains:
- `id` instead of `payment_id`
- `status` instead of `payment_status` (in some cases)

Example of new API response:
```json
{
    "id": "4957197073",
    "token_id": "5603669597",
    "order_id": "user_7480108404_1751204217",
    "invoice_url": "https://nowpayments.io/payment/?iid=4957197073",
    "price_amount": "12.36",
    "price_currency": "USD",
    "pay_currency": "USDTTRC20",
    "created_at": "2025-06-29T13:36:57.622Z",
    "updated_at": "2025-06-29T13:36:57.622Z"
}
```

## Solution Implemented

### 1. NowPayments Adapter (`nowpayments_adapter.py`)

Created a centralized adapter to handle both old and new API formats:

```python
class NowPaymentsAdapter:
    @staticmethod
    def extract_payment_id(data: Dict[str, Any]) -> Optional[str]:
        # Try both old and new API formats
        payment_id = data.get("payment_id") or data.get("id")
        return payment_id
    
    @staticmethod
    def extract_payment_status(data: Dict[str, Any]) -> Optional[str]:
        # Try both old and new API formats
        status = data.get("payment_status") or data.get("status")
        return status
```

### 2. Updated Payment Processing

Modified `payment.py` to use the adapter:

```python
# Before
payment_id = data.get("payment_id")
invoice_url = data.get("invoice_url")

# After
is_valid, error_msg, payment_id, invoice_url = nowpayments_adapter.validate_invoice_response(data)
```

### 3. Updated Webhook Processing

Modified webhook handling to use the adapter:

```python
# Before
payment_id = data.get("payment_id") or data.get("id")
payment_status = data.get("payment_status")

# After
is_valid, error_msg, payment_id, payment_status = nowpayments_adapter.validate_webhook_payload(data)
```

### 4. Updated Payment Monitoring

Modified `payment_monitor.py` to use the adapter:

```python
# Before
new_status = payment_info.get("payment_status") or payment_info.get("status")

# After
new_status = nowpayments_adapter.extract_payment_status(payment_info)
```

## Files Modified

1. **`payment.py`**
   - Updated `create_invoice()` function
   - Updated `verify_payment()` function
   - Updated `process_webhook()` function

2. **`payment_monitor.py`**
   - Updated payment status checking
   - Added adapter import

3. **`payment_status.py`**
   - Updated payment status verification
   - Added adapter import

4. **`nowpayments_adapter.py`** (New)
   - Centralized adapter for API response handling
   - Validation functions
   - Error handling

5. **`test_nowpayments_adapter.py`** (New)
   - Test script for adapter functionality
   - Tests both old and new API formats

## Testing

Run the adapter test to verify functionality:

```bash
python test_nowpayments_adapter.py
```

Expected output:
```
🧪 Testing NowPayments Adapter...
✅ Extracted Payment ID: 4957197073
✅ Extracted Invoice URL: https://nowpayments.io/payment/?iid=4957197073
✅ Invoice Response Valid: True
✅ Webhook Payload Valid: True
✅ Webhook Payment ID: 4957197073
✅ Webhook Status: confirmed
```

## Benefits

1. **Backward Compatibility**: Works with both old and new API formats
2. **Centralized Logic**: All API response handling in one place
3. **Better Error Handling**: Clear error messages for missing fields
4. **Easy Maintenance**: Future API changes only need adapter updates
5. **Comprehensive Testing**: Test coverage for all scenarios

## Future Considerations

1. **API Version Detection**: Automatically detect API version
2. **Field Mapping**: Configurable field mappings
3. **Response Validation**: More comprehensive validation
4. **Performance Monitoring**: Track API response times
5. **Error Recovery**: Automatic retry with different formats

## Troubleshooting

### Common Issues

1. **Still Getting Missing Payment ID Error**
   - Check if adapter is properly imported
   - Verify API response format
   - Run adapter tests

2. **Webhook Processing Fails**
   - Check webhook payload format
   - Verify signature validation
   - Review webhook logs

3. **Payment Status Not Updating**
   - Check payment verification
   - Verify database updates
   - Review monitor logs

### Debug Commands

```bash
# Test adapter functionality
python test_nowpayments_adapter.py

# Test payment creation
python -c "from payment import create_invoice; print(create_invoice(10, 12345))"

# Test webhook processing
python -c "from payment import process_webhook; print(process_webhook('{}', 'test'))"
```

## Migration Guide

### For Existing Installations

1. **Update Files**: Replace modified files with new versions
2. **Test Adapter**: Run `test_nowpayments_adapter.py`
3. **Test Payment**: Create a test payment
4. **Monitor Logs**: Check for any remaining errors
5. **Update Documentation**: Review this guide

### For New Installations

1. **Install Dependencies**: Ensure all required packages
2. **Configure API**: Set up NowPayments API key
3. **Test Integration**: Run all test scripts
4. **Deploy**: Start the bot with monitoring

## Support

For issues related to NowPayments API integration:
- Check adapter test results
- Review payment creation logs
- Verify API key configuration
- Contact support: @Abul_kalam2025

## Conclusion

The NowPayments API adapter provides a robust solution for handling API format changes while maintaining backward compatibility. This ensures reliable payment processing regardless of API version changes. 