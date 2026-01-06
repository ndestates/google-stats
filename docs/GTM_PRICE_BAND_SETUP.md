# Google Tag Manager - Dynamic Price Band Tracking Setup

## Overview
This setup automatically tracks which price band a property belongs to and sends it to GA4, allowing you to create audiences without manually updating GTM for each new property.

## Implementation Steps

### 1. Create Custom JavaScript Variable: "Property Price"

**Variable Type:** Custom JavaScript  
**Variable Name:** `JS - Property Price`

```javascript
function() {
  // Try to get price from data layer first
  if (window.dataLayer) {
    for (var i = dataLayer.length - 1; i >= 0; i--) {
      if (dataLayer[i].propertyPrice) {
        return parseInt(dataLayer[i].propertyPrice);
      }
    }
  }
  
  // Fallback: Extract from page content
  // Method 1: Look for meta tag
  var metaPrice = document.querySelector('meta[property="product:price:amount"]');
  if (metaPrice) {
    return parseInt(metaPrice.getAttribute('content'));
  }
  
  // Method 2: Look for schema.org structured data
  var schemaScript = document.querySelector('script[type="application/ld+json"]');
  if (schemaScript) {
    try {
      var schema = JSON.parse(schemaScript.textContent);
      if (schema.offers && schema.offers.price) {
        return parseInt(schema.offers.price);
      }
    } catch(e) {}
  }
  
  // Method 3: Extract from visible price element
  var priceElement = document.querySelector('.property-price, .price, [itemprop="price"]');
  if (priceElement) {
    var priceText = priceElement.textContent.replace(/[£,\s]/g, '');
    var price = parseInt(priceText);
    if (!isNaN(price)) {
      return price;
    }
  }
  
  return undefined;
}
```

### 2. Create Custom JavaScript Variable: "Price Band"

**Variable Type:** Custom JavaScript  
**Variable Name:** `JS - Price Band`

```javascript
function() {
  // Get the property price
  var price = {{JS - Property Price}};
  
  if (!price || isNaN(price)) {
    return undefined;
  }
  
  // Define price bands
  if (price < 200000) {
    return 'Under £200K';
  } else if (price >= 200000 && price < 400000) {
    return '£200K-400K';
  } else if (price >= 400000 && price < 600000) {
    return '£400K-600K';
  } else if (price >= 600000 && price < 800000) {
    return '£600K-800K';
  } else if (price >= 800000 && price < 1000000) {
    return '£800K-1M';
  } else if (price >= 1000000) {
    return '£1M+';
  }
  
  return undefined;
}
```

### 3. Create Custom JavaScript Variable: "Property Type"

**Variable Type:** Custom JavaScript  
**Variable Name:** `JS - Property Type`

```javascript
function() {
  // Check URL for property type
  var url = window.location.href.toLowerCase();
  
  if (url.indexOf('/to-rent/') > -1 || url.indexOf('/rent/') > -1) {
    return 'rent';
  } else if (url.indexOf('/for-sale/') > -1 || url.indexOf('/buy/') > -1) {
    return 'buy';
  }
  
  // Fallback: Check page content
  var typeElement = document.querySelector('[data-property-type]');
  if (typeElement) {
    return typeElement.getAttribute('data-property-type').toLowerCase();
  }
  
  // Default to buy
  return 'buy';
}
```

### 4. Create Trigger: "Property Page View"

**Trigger Type:** Page View - DOM Ready  
**Trigger Name:** `Trigger - Property Page View`

**This trigger fires on:**
- Some DOM Ready Events

**Fire this trigger when an Event occurs and all of these conditions are true:**

- Page URL matches RegEx: `.*/properties/.*`
- {{JS - Property Price}} does not equal `undefined`

### 5. Create GA4 Event Tag: "Property View with Price Band"

**Tag Type:** Google Analytics: GA4 Event  
**Tag Name:** `GA4 - Property View with Price Band`

**Configuration:**
- **Measurement ID:** Your GA4 Measurement ID
- **Event Name:** `view_property`

**Event Parameters:**
- **Parameter Name:** `price_band`  
  **Value:** `{{JS - Price Band}}`

- **Parameter Name:** `property_price`  
  **Value:** `{{JS - Property Price}}`

- **Parameter Name:** `property_type`  
  **Value:** `{{JS - Property Type}}`

- **Parameter Name:** `page_location`  
  **Value:** `{{Page URL}}`

**Triggering:**
- Trigger: `Trigger - Property Page View`

### 6. Create GA4 Event Tag: "Enhanced Page View"

**Tag Type:** Google Analytics: GA4 Event  
**Tag Name:** `GA4 - Enhanced Page View`

This sends the price_band as a user property for audience building.

**Configuration:**
- **Measurement ID:** Your GA4 Measurement ID
- **Event Name:** `page_view`

**User Properties:**
- **Property Name:** `last_viewed_price_band`  
  **Value:** `{{JS - Price Band}}`

- **Property Name:** `last_viewed_property_type`  
  **Value:** `{{JS - Property Type}}`

**Triggering:**
- Trigger: `Trigger - Property Page View`

---

## Alternative: Data Layer Push (Recommended if you control the website code)

If you can modify your website code, add this to your property pages:

```javascript
<script>
  window.dataLayer = window.dataLayer || [];
  window.dataLayer.push({
    'event': 'propertyView',
    'propertyPrice': 450000,  // Dynamic from your backend
    'propertyType': 'buy',     // 'buy' or 'rent'
    'propertyReference': 'ABC123'
  });
</script>
```

Then simplify the GTM variables to just read from dataLayer:

```javascript
// JS - Property Price (simplified)
function() {
  return {{DLV - propertyPrice}};  // Use built-in Data Layer Variable
}
```

---

## Creating Audiences in GA4

Once GTM is deployed and collecting data:

### 1. Register Custom Dimension

1. Go to GA4 → **Admin** → **Custom Definitions** → **Custom Dimensions**
2. Click **Create custom dimension**
3. **Dimension name:** `price_band`
4. **Scope:** Event
5. **Event parameter:** `price_band`
6. Click **Save**

### 2. Create Audiences

1. Go to GA4 → **Admin** → **Audiences**
2. Click **New audience**
3. Click **Create a custom audience**
4. Add conditions:
   - **Event name** = `view_property`
   - **price_band** = `£200K-400K` (or whichever band you want)
5. Set **Membership duration:** 30 days
6. Name it: `[Price Band] £200K-400K`
7. Click **Save**

Repeat for each price band.

---

## Testing

### 1. Preview Mode
1. In GTM, click **Preview**
2. Enter your property page URL
3. Check that:
   - Variables `JS - Property Price` and `JS - Price Band` are populated
   - Tag `GA4 - Property View with Price Band` fires
   - Event parameters are correct

### 2. GA4 DebugView
1. Go to GA4 → **Admin** → **DebugView**
2. Visit a property page in preview mode
3. Check for `view_property` event
4. Verify `price_band` parameter is correct

### 3. Real-Time Report
1. Go to GA4 → **Reports** → **Realtime**
2. Visit a property page
3. Check that events are appearing

---

## Benefits of This Approach

✅ **Fully Dynamic** - No GTM updates needed when new properties are added  
✅ **Automatic Price Bands** - Properties automatically assigned to correct band  
✅ **Future-Proof** - Works for any price in any band  
✅ **Multiple Use Cases** - Can create audiences by price, type, or combinations  
✅ **Flexible** - Easy to add new bands or change thresholds in GTM

---

## Troubleshooting

### Price not being captured?

1. Check your page's HTML structure
2. Update the CSS selectors in `JS - Property Price` to match your site
3. Add console logging to debug:

```javascript
function() {
  var price = {{JS - Property Price}};
  console.log('Property Price:', price);
  return price;
}
```

### Events not showing in GA4?

1. Check GTM Preview mode to ensure tags fire
2. Verify GA4 Measurement ID is correct
3. Check browser console for errors
4. Wait 24-48 hours for custom dimensions to populate

---

## Next Steps

1. **Deploy** this GTM configuration
2. **Wait 24-48 hours** for data collection
3. **Create audiences** in GA4 for each price band
4. **Link to Google Ads** for remarketing campaigns
