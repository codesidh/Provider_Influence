# Power BI Template Structure for Provider Influence Dashboard

## 🎯 Template Overview
This document provides the exact structure to create a Power BI Template (.pbit) file that you can save and reuse.

## 📋 Step-by-Step Template Creation

### Phase 1: Create the Basic Structure in Power BI Desktop

#### 1.1 Start New Report
1. Open Power BI Desktop
2. Create a new blank report
3. Save it as "Provider_Influence_Dashboard_Template.pbix"

#### 1.2 Create Data Model Structure (No Data Import Yet)
1. Go to **Model** view
2. Create these empty tables with proper structure:

**Calendar_Table:**
```
- Date (Date)
- Year (Whole Number)
- Month (Whole Number)
- Month Name (Text)
- Quarter (Whole Number)
- Quarter Name (Text)
- Year Month (Text)
- Is Current Month (True/False)
- Is Current Year (True/False)
```

**Provider_Data:**
```
- Provider ID (Text)
- Provider Name (Text)
- Tax ID (Text)
- Provider Organisation Name (Text)
- NPI (Text)
- Taxonomy (Text)
- Provider Entity (Text)
- Provider Type (Text)
- Organisation Type (Text)
- Provider Specialty (Text)
- Provider Status (Text)
- Auth Year Month (Text)
- Member Count (Decimal Number)
- Provider Relationship Specialist Name (Text)
- Auth Year Month Date (Date)
- Year (Whole Number)
- Month (Whole Number)
```

**Authorization_Data:**
```
- Member ID (Text)
- Procedure Code (Text)
- Auth Month (Text)
- Approved Units (Decimal Number)
- Frequency (Text)
- Total Cost (Decimal Number)
- Provider ID (Text)
- Auth Month Date (Date)
- Year (Whole Number)
- Month (Whole Number)
```

**LTSS_Procedure_Mapping:**
```
- Procedure Code (Text)
- Procedure Description (Text)
- IS_LTSS (True/False)
- LTSS_Category (Text)
```

**LTSS_Summary:**
```
- LTSS_Category (Text)
- Total_Cost (Decimal Number)
- Total_Units (Decimal Number)
- Unique_Members (Whole Number)
- Procedure_Count (Whole Number)
- Cost_Per_Member (Decimal Number)
```

**Provider_Summary:**
```
- Provider ID (Text)
- Provider Name (Text)
- Total_Cost (Decimal Number)
- Total_Units (Decimal Number)
- Unique_Members (Whole Number)
- LTSS_Total_Cost (Decimal Number)
- LTSS_Total_Units (Decimal Number)
- LTSS_Unique_Members (Whole Number)
- LTSS_Cost_Share (Decimal Number)
- Cost_Per_Unit (Decimal Number)
```

**Member_Analytics:**
```
- Member ID (Text)
- Total_Cost (Decimal Number)
- Total_Units (Decimal Number)
- Provider_Count (Whole Number)
- Procedure_Count (Whole Number)
- LTSS_Total_Cost (Decimal Number)
- LTSS_Total_Units (Decimal Number)
- LTSS_Cost_Share (Decimal Number)
- Cost_Per_Month (Decimal Number)
```

#### 1.3 Set Up Relationships
Create these relationships in the Model view:

```
1. Provider_Data[Provider ID] (1) ←→ (*) Authorization_Data[Provider ID]
   - Cardinality: One to Many
   - Cross filter direction: Single
   - Make this relationship active: Yes

2. Calendar_Table[Date] (1) ←→ (*) Authorization_Data[Auth Month Date]
   - Cardinality: One to Many
   - Cross filter direction: Single
   - Make this relationship active: No

3. Calendar_Table[Date] (1) ←→ (*) Provider_Data[Auth Year Month Date]
   - Cardinality: One to Many
   - Cross filter direction: Single
   - Make this relationship active: No

4. LTSS_Procedure_Mapping[Procedure Code] (1) ←→ (*) Authorization_Data[Procedure Code]
   - Cardinality: One to Many
   - Cross filter direction: Single
   - Make this relationship active: No
```

### Phase 2: Create Calculated Columns

#### 2.1 Authorization_Data Calculated Columns
Add these calculated columns to the Authorization_Data table:

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

**Auth Month Date:**
```dax
Auth Month Date = 
DATE(
    VALUE(LEFT(Authorization_Data[Auth Month], 4)),
    VALUE(RIGHT(Authorization_Data[Auth Month], 2)),
    1
)
```

#### 2.2 Provider_Data Calculated Columns
Add this calculated column to the Provider_Data table:

**Auth Year Month Date:**
```dax
Auth Year Month Date = 
DATE(
    VALUE(LEFT(Provider_Data[Auth Year Month], 4)),
    VALUE(RIGHT(Provider_Data[Auth Year Month], 2)),
    1
)
```

### Phase 3: Create Core DAX Measures

#### 3.1 Core Metrics
Create these measures in a new measure group called "Core Metrics":

**Total Members:**
```dax
Total Members = 
DISTINCTCOUNT(Provider_Data[Provider ID])
```

**Total Cost:**
```dax
Total Cost = 
SUM(Authorization_Data[Total Cost])
```

**Total Units:**
```dax
Total Units = 
SUM(Authorization_Data[Approved Units])
```

**Total Authorizations:**
```dax
Total Authorizations = 
COUNTROWS(Authorization_Data)
```

#### 3.2 LTSS Metrics
Create these measures in a new measure group called "LTSS Metrics":

**LTSS Total Cost:**
```dax
LTSS Total Cost = 
CALCULATE(
    [Total Cost],
    Authorization_Data[Is LTSS] = "LTSS"
)
```

**LTSS Penetration Rate:**
```dax
LTSS Penetration Rate = 
DIVIDE(
    [LTSS Total Cost],
    [Total Cost],
    0
)
```

**LTSS Cost Share:**
```dax
LTSS Cost Share = 
DIVIDE(
    [LTSS Total Cost],
    [Total Cost],
    0
)
```

**LTSS Authorization Count:**
```dax
LTSS Authorization Count = 
CALCULATE(
    [Total Authorizations],
    Authorization_Data[Is LTSS] = "LTSS"
)
```

#### 3.3 Provider Metrics
Create these measures in a new measure group called "Provider Metrics":

**Provider Market Share:**
```dax
Provider Market Share = 
DIVIDE(
    [Total Cost],
    CALCULATE([Total Cost], ALL(Provider_Data)),
    0
)
```

**Provider LTSS Concentration:**
```dax
Provider LTSS Concentration = 
CALCULATE(
    [LTSS Cost Share],
    ALL(Authorization_Data)
)
```

**Provider Efficiency Score:**
```dax
Provider Efficiency Score = 
DIVIDE(
    [Total Cost],
    [Total Units],
    0
)
```

#### 3.4 Financial Metrics
Create these measures in a new measure group called "Financial Metrics":

**PMPM (Per Member Per Month):**
```dax
PMPM = 
DIVIDE(
    [Total Cost],
    [Total Members],
    0
)
```

**LTSS PMPM:**
```dax
LTSS PMPM = 
CALCULATE(
    [PMPM],
    Authorization_Data[Is LTSS] = "LTSS"
)
```

**Cost per Unit:**
```dax
Cost per Unit = 
DIVIDE(
    [Total Cost],
    [Total Units],
    0
)
```

### Phase 4: Create Dashboard Pages Structure

#### 4.1 Executive Summary Page
Create this page with placeholder visuals:

**KPI Cards:**
- Card visual for Total Members
- Card visual for Total Cost
- Card visual for LTSS Penetration Rate
- Card visual for YOY Growth Rate

**Trend Charts:**
- Line chart for Member Growth Over Time
- Line chart for Cost Trends by Month
- Line chart for LTSS vs Non-LTSS Trends

**Filters:**
- Slicer for Date Range
- Slicer for Provider Type

#### 4.2 Provider Performance Page
Create this page with placeholder visuals:

**Matrix Table:**
- Matrix visual with Provider Name as rows
- Columns: Provider Type, Provider Specialty
- Values: Total Cost, Member Count, LTSS Cost Share, Efficiency Score

**Scatter Plot:**
- Scatter chart with Total Cost on X-axis
- Efficiency Score on Y-axis
- Member Count as size
- Provider Type as color

**Bar Charts:**
- Bar chart for Provider Specialty Comparison
- Bar chart for Entity Type Analysis
- Bar chart for Provider Status Distribution

#### 4.3 LTSS Deep Dive Page
Create this page with placeholder visuals:

**Donut Chart:**
- Donut chart for LTSS vs Non-LTSS Cost Distribution

**Stacked Bar Chart:**
- Stacked bar chart for LTSS Cost by Category

**Line Chart:**
- Line chart for LTSS Penetration Trends Over Time

**Matrix Table:**
- Matrix visual for LTSS Categories with Procedure Codes

#### 4.4 Member Analytics Page
Create this page with placeholder visuals:

**Funnel Chart:**
- Funnel chart for Member Journey Through Care Levels

**Cohort Analysis:**
- Matrix visual for Member Retention Patterns

**Box Plot:**
- Box and whisker chart for Member Cost Distribution by Provider

#### 4.5 Financial Analytics Page
Create this page with placeholder visuals:

**PMPM Trends:**
- Line chart for PMPM trends over time

**Pareto Chart:**
- Column chart with cumulative line for Provider cost concentration

**Forecasting:**
- Line chart with trend lines for predictive cost modeling

### Phase 5: Save as Template

#### 5.1 Final Template Preparation
1. Remove any sample data (if any was added)
2. Ensure all relationships are properly set
3. Verify all calculated columns and measures are created
4. Check that all pages have placeholder visuals

#### 5.2 Save Template
1. Go to **File** → **Save As**
2. Choose **Power BI Template (*.pbit)** as the file type
3. Save as "Provider_Influence_Dashboard_Template.pbit"
4. Add a description: "Provider Influence Power BI Dashboard Template with complete data model, measures, and page structure"

## 🎯 Template Usage Instructions

### For You (Template Creator):
1. Follow all steps above to create the template
2. Test the template by opening it and verifying structure
3. Share the .pbit file with your team

### For Template Users:
1. Open the .pbit file in Power BI Desktop
2. Import your CSV data files
3. The structure, measures, and page layout will be preserved
4. Customize visuals and add your specific data

## 🔧 Template Benefits

- **Consistent Structure**: Ensures all users follow the same data model
- **Reusable**: Can be used for multiple implementations
- **Training Tool**: Helps team members learn the dashboard structure
- **Version Control**: Easy to maintain and update
- **Standardization**: Ensures consistent dashboard development across teams

## 📊 Next Steps After Template Creation

1. **Test the Template**: Open it and verify all components
2. **Import Your Data**: Use the CSV files from the data/ directory
3. **Customize Visuals**: Adjust charts and layouts as needed
4. **Test Performance**: Verify all measures work correctly
5. **Share with Team**: Distribute the template for consistent development

---

*Template Structure Created: 2024-12-19*
*Provider Influence Power BI Dashboard - Enterprise Template*
