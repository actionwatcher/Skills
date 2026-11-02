---
name: oshpark-order
description: Prepare OSH Park quotes and unpaid orders for printed circuit boards. The user enters passwords and makes payments. Use for file uploads, delivery options, and order status checks.
---

# OSH Park Orders

## Get the order requirements

1. Identify the design revision and its ZIP archive.
2. Examine the design check results before the upload.
3. Get the quantity and the delivery requirements from the conversation.
4. If necessary, get the destination country and postal code for a delivery quote.
5. Get the prices and manufacturing limits from [OSH Park](https://oshpark.com/).

Use the user's decisions from the conversation.
For a quote only, stop before you make an order.
Do not use personal data from a different project.
Do not make a panel if the single board meets the manufacturing limits.

## Upload the files

1. Upload the specified ZIP archive.
2. Compare the detected dimensions with the design dimensions.
3. Compare the detected copper layer count with the design.
4. Examine the manufacturer's images of both sides.
5. Do a check of the outline, holes, copper, and solder mask.
6. Find the cause of each error before you continue.
7. Enter the project name.
8. Enter only the email address that the user gives for OSH Park.

## Let the user sign in

1. Open the OSH Park sign-in page when necessary.
2. Ask the user to sign in directly on that page.
3. Stop browser observation until the user completes sign-in.
4. Then, make sure that OSH Park shows the correct account.

Do not get passwords or verification codes through chat.
Do not read password manager records.
Do not save passwords or session cookies.
Let the user select persistent sign-in, if they want it.
Let the user complete CAPTCHA and password reset procedures.

Sign-in on a separate device does not sign in the automation browser.
After sign-in in the automation browser, the assistant can see the OSH Park account pages.

## Prepare the unpaid order

1. Add the specified board to the cart.
2. Set the quantity.
3. Make sure that the page shows the new quantity and the new total.
4. Select other services only with the user's agreement.
5. Open checkout.
6. Tell the user to enter the delivery address directly on the page.
7. Get the delivery rates.
8. Examine any address corrections before acceptance.
9. Select the delivery service that meets the user's requirements.
10. Do a check of the revision, quantity, delivery cost, and total.

If delivery has no cost, use that service when it is satisfactory for the user.
If the total is more than the user's limit, get the user's decision before you continue.

Make an unpaid order only for an order task.
Before submission, make sure that the action cannot charge a stored payment method.
If the effect of submission is not known, let the user complete checkout.

## User payment

1. Give the user the OSH Park order link and the total.
2. Tell the user to make the payment on their phone or in their own browser.
3. Stop observation of all payment pages.
4. After the user reports completion, open only the OSH Park order page.
5. Read the payment status on that page.
6. Give the user the quantity, total, and production status.

Do not open PayPal or a card payment form.
Do not enter payment data.
Do not make a payment.
If payment is pending, tell the user.
Do not make another payment attempt.

Save the order number, revision, quantity, total, delivery service, order link, and status.
Do not save passwords, payment tokens, payment identifiers, full addresses, or phone numbers.

## Recover from a page error

1. Read the page before each upload or order submission.
2. If an order exists, use the order history to find it.
3. If no order exists, upload the same files once more.
4. If that upload fails, examine the error before another upload.

If a form is not active, examine the fields for missing data.
Use normal typing or the Enter key when necessary.
Do not remove controls that prevent form submission.
After a quantity change, wait for the new total.
If you do not know the submission result, examine the order history before another attempt.
Do not make a duplicate order.
