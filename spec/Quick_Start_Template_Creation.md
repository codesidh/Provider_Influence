# 🚀 Quick Start: Create Power BI Template in 30 Minutes

## ⚡ Essential Steps to Create Your .pbit File

### **Step 1: Open Power BI Desktop (5 minutes)**
1. Launch Power BI Desktop
2. Create new blank report
3. Save as "Provider_Influence_Dashboard_Template.pbix"

### **Step 2: Create Data Model Structure (10 minutes)**
1. Go to **Model** view
2. Click **New Table** and create these empty tables:

**Quick Table Creation:**
```
Calendar_Table: Date, Year, Month, Month Name, Quarter, Quarter Name, Year Month, Is Current Month, Is Current Year
Provider_Data: Provider ID, Provider Name, Provider Type, Provider Specialty, Provider Status, Auth Year Month, Member Count, Auth Year Month Date, Year, Month
Authorization_Data: Member ID, Procedure Code, Auth Month, Approved Units, Total Cost, Provider ID, Auth Month Date, Year, Month
LTSS_Procedure_Mapping: Procedure Code, Procedure Description, IS_LTSS, LTSS_Category
LTSS_Summary: LTSS_Category, Total_Cost, Total_Units, Unique_Members, Procedure_Count, Cost_Per_Member
Provider_Summary: Provider ID, Provider Name, Total_Cost, Total_Units, Unique_Members, LTSS_Total_Cost, LTSS_Total_Units, LTSS_Unique_Members, LTSS_Cost_Share, Cost_Per_Unit
Member_Analytics: Member ID, Total_Cost, Total_Units, Provider_Count, Procedure_Count, LTSS_Total_Cost, LTSS_Total_Units, LTSS_Cost_Share, Cost_Per_Month
```

### **Step 3: Set Up Relationships (5 minutes)**
In Model view, create these 4 key relationships:
```
1. Provider_Data[Provider ID] → Authorization_Data[Provider ID] (1:Many, Active)
2. Calendar_Table[Date] → Authorization_Data[Auth Month Date] (1:Many, Not Active)
3. Calendar_Table[Date] → Provider_Data[Auth Year Month Date] (1:Many, Not Active)
4. LTSS_Procedure_Mapping[Procedure Code] → Authorization_Data[Procedure Code] (1:Many, Not Active)
```

### **Step 4: Add Key Calculated Columns (5 minutes)**
Add these to Authorization_Data table:

**Is LTSS:**
```dax
Is LTSS = 
SWITCH(
    TRUE(),
    Authorization_Data[Procedure Code] IN {"T1019", "S5125", "T2025", "S5150", "S5151"}, "LTSS",
    Authorization_Data[Procedure Code] IN {"99401", "99402"}, "Preventive",
    "Non-LTSS"
)
```

**LTSS Category:**
```dax
LTSS Category = 
LOOKUPVALUE(
    LTSS_Procedure_Mapping[LTSS_Category],
    LTSS_Procedure_Mapping[Procedure Code],
    Authorization_Data[Procedure Code]
)
```

### **Step 5: Create Essential Measures (5 minutes)**
Add these core measures:

**Total Cost:**
```dax
Total Cost = SUM(Authorization_Data[Total Cost])
```

**LTSS Total Cost:**
```dax
LTSS Total Cost = 
CALCULATE([Total Cost], Authorization_Data[Is LTSS] = "LTSS")
```

**LTSS Penetration Rate:**
```dax
LTSS Penetration Rate = 
DIVIDE([LTSS Total Cost], [Total Cost], 0)
```

### **Step 6: Save as Template**
1. **File** → **Save As**
2. Choose **Power BI Template (*.pbit)**
3. Save as "Provider_Influence_Dashboard_Template.pbit"
4. Add description: "Provider Influence Dashboard Template"

## 🎯 **What You Get:**

✅ **Complete Data Model Structure**
✅ **All Required Tables & Relationships**
✅ **Essential DAX Measures**
✅ **Calculated Columns for LTSS Analysis**
✅ **Professional Template File (.pbit)**

## 📊 **After Creating Template:**

1. **Open the .pbit file**
2. **Import your CSV data** from the `data/` directory
3. **All structure is preserved** - just add your data!
4. **Build visuals** using the existing measures

## 🔥 **Pro Tips:**

- **Don't add sample data** - keep tables empty for template
- **Test relationships** before saving as template
- **Verify measures** work with empty tables
- **Use consistent naming** conventions

---

**Time to Complete: ~30 minutes**
**Result: Professional .pbit template file**
**Reusable: Yes, for multiple implementations**

*This template will save you hours of setup time for future dashboard projects!*
