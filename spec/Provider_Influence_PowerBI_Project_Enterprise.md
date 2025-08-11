# Provider Influence Power BI Dashboard - Enterprise Implementation Guide

## 🏗️ Enterprise Architecture Considerations

### Data Governance & Security
- **Row-Level Security (RLS)**: Implement provider-specific access controls
- **Data Classification**: Mark PII/PHI fields appropriately
- **Audit Trail**: Track dashboard usage and data access patterns
- **Refresh Strategy**: Implement incremental refresh for large datasets

### Performance Optimization
- **Composite Models**: Consider DirectQuery for real-time data needs
- **Aggregations**: Pre-calculate summary tables for faster performance
- **Partitioning**: Implement date-based partitioning for historical data
- **Compression**: Optimize data types and remove unnecessary columns

## 📊 CSV-Based Data Model Architecture

### Primary CSV Files (As Provided)

#### 1. **provider_data.csv** - Provider master and monthly member counts
| Column Name | Data Type | Description |
|-------------|-----------|-------------|
| Provider ID | Text | Unique provider identifier |
| Provider Name | Text | Provider business name |
| Tax ID | Text | Provider tax identification number |
| Provider Organisation Name | Text | Organization/entity name |
| NPI | Text | National Provider Identifier |
| Taxonomy | Text | Provider taxonomy classification |
| Provider Entity | Text | Entity type (Individual, Organization, etc.) |
| Provider Type | Text | Type classification |
| Organisation Type | Text | Organization category |
| Provider Specialty | Text | Medical/service specialty |
| Provider Status | Text | Active/Inactive status |
| Auth Year Month | Text | Year-month format (yyyy-mm) |
| Member Count | Number | Monthly member count for provider |
| Provider Relationship Specialist Name | Text | Assigned relationship manager |

#### 2. **authorization_data.csv** - Authorization-level detail including LTSS codes
| Column Name | Data Type | Description |
|-------------|-----------|-------------|
| Member ID | Text | Unique member identifier |
| Procedure Code | Text | Service procedure code (CPT/HCPCS) |
| Auth Month | Text | Authorization month (yyyy-mm format) |
| Approved Units | Number | Number of approved service units |
| Frequency | Text | Service frequency description |
| Total Cost | Currency | Total authorized cost amount |
| Provider ID | Text | Provider identifier (links to provider_data) |

#### 3. **ltss_procedure_mapping.csv** - LTSS Procedure Code Classification
| Column Name | Data Type | Description |
|-------------|-----------|-------------|
| Procedure Code | Text | Service procedure code (matches authorization_data) |
| Procedure Description | Text | Detailed description of the procedure/service |
| IS_LTSS | Text | Flag indicating LTSS status (Yes/No) |
| LTSS_Category | Text | LTSS service category classification |

### Additional Calculated Tables (Created in Power BI)
4. **Calendar_Table** - Generated date dimension
5. **MonthlyProviderSummary** - Aggregated provider metrics
6. **ProviderHierarchy** - Provider drill-down structure

### Key Calculated Columns to Add
```dax
// Add to authorization_data table
Is LTSS = 
SWITCH(
    TRUE(),
    authorization_data[Procedure Code] IN {"T1019", "S5125", "T2025", "S5150", "S5151"}, "LTSS",
    authorization_data[Procedure Code] IN {"99401", "99402"}, "Preventive",
    "Non-LTSS"
)

// Add to provider_data table (if needed)
Auth Year Month Date = 
DATE(
    VALUE(LEFT(provider_data[Auth Year Month], 4)),
    VALUE(RIGHT(provider_data[Auth Year Month], 2)),
    1
)

// Add to authorization_data table (if needed)
Auth Month Date = 
DATE(
    VALUE(LEFT(authorization_data[Auth Month], 4)),
    VALUE(RIGHT(authorization_data[Auth Month], 2)),
    1
)
```

### Relationships for CSV Files
```
provider_data[Provider ID] (1) ←→ (*) authorization_data[Provider ID]
Calendar_Table[Date] (1) ←→ (*) authorization_data[Auth Month Date]
Calendar_Table[Date] (1) ←→ (*) provider_data[Auth Year Month Date]
LTSS_ProcedureCodes[Procedure Code] (1) ←→ (*) authorization_data[Procedure Code]
```

### Data Quality Considerations
- **Provider ID**: Ensure consistent formatting between provider_data.csv and authorization_data.csv
- **Procedure Code**: Must match exactly between authorization_data.csv and ltss_procedure_mapping.csv
- **Date Formats**: Standardize yyyy-mm format across both main files
- **LTSS Mapping**: Validate that all procedure codes in authorization_data exist in ltss_procedure_mapping.csv
- **IS_LTSS Values**: Should only contain "Yes" or "No" values
- **LTSS_Category**: Ensure consistent category naming (no typos or variations)
- **Member ID**: Check for proper anonymization/de-identification
- **Numeric Fields**: Ensure proper formatting for Member Count, Approved Units, Total Cost
- **Missing Values**: Handle NULL/blank values in the mapping table appropriately

## 🧮 Enhanced DAX Measures Library

### Core Member Metrics
```dax
// Total Unique Members
Total Members = 
DISTINCTCOUNT(authorization_data[Member ID])

// Active Members (with authorizations in selected period)
Active Members = 
CALCULATE(
    DISTINCTCOUNT(authorization_data[Member ID]),
    authorization_data[Approved Units] > 0
)

// New Members (first authorization in selected period)
New Members = 
VAR MinAuthDate = MIN(Calendar_Table[Date])
VAR MaxAuthDate = MAX(Calendar_Table[Date])
RETURN
CALCULATE(
    DISTINCTCOUNT(authorization_data[Member ID]),
    FILTER(
        ALL(Calendar_Table),
        CALCULATE(MIN(authorization_data[Auth Month])) >= FORMAT(MinAuthDate, "yyyy-mm") &&
        CALCULATE(MIN(authorization_data[Auth Month])) <= FORMAT(MaxAuthDate, "yyyy-mm")
    )
)

// Member Count from Provider File
Provider Member Count = 
SUM(provider_data[Member Count])
```

### LTSS-Specific Measures (Updated for Mapping Table)
```dax
// LTSS Member Penetration Rate (using mapping table)
LTSS Penetration Rate = 
DIVIDE(
    CALCULATE(DISTINCTCOUNT(authorization_data[Member ID]), 
        RELATED(ltss_procedure_mapping[IS_LTSS]) = "Yes"),
    [Total Members],
    0
)

// LTSS Cost Share (using mapping table)
LTSS Cost Share = 
DIVIDE(
    [LTSS Total Cost],
    [Total Cost],
    0
)

// Average LTSS Units per Member (using mapping table)
Avg LTSS Units per Member = 
DIVIDE(
    CALCULATE(SUM(authorization_data[Approved Units]), 
        RELATED(ltss_procedure_mapping[IS_LTSS]) = "Yes"),
    CALCULATE(DISTINCTCOUNT(authorization_data[Member ID]), 
        RELATED(ltss_procedure_mapping[IS_LTSS]) = "Yes"),
    0
)

// LTSS Total Cost (Enhanced with mapping table)
LTSS Total Cost = 
CALCULATE(
    SUM(authorization_data[Total Cost]),
    RELATED(ltss_procedure_mapping[IS_LTSS]) = "Yes"
)

// Total Cost
Total Cost = 
SUM(authorization_data[Total Cost])

// LTSS Cost by Category
LTSS Cost by Category = 
CALCULATE(
    SUM(authorization_data[Total Cost]),
    RELATED(ltss_procedure_mapping[IS_LTSS]) = "Yes"
)

// Non-LTSS Cost
Non-LTSS Cost = 
CALCULATE(
    SUM(authorization_data[Total Cost]),
    RELATED(ltss_procedure_mapping[IS_LTSS]) = "No"
)

// LTSS Authorization Count
LTSS Authorization Count = 
CALCULATE(
    COUNTROWS(authorization_data),
    RELATED(ltss_procedure_mapping[IS_LTSS]) = "Yes"
)

// Average Cost per LTSS Authorization
Avg Cost per LTSS Auth = 
DIVIDE(
    [LTSS Total Cost],
    [LTSS Authorization Count],
    0
)
```

### Provider Influence Metrics
```dax
// Provider Market Share
Provider Market Share = 
DIVIDE(
    [Total Cost],
    CALCULATE([Total Cost], REMOVEFILTERS(provider_data)),
    0
)

// Provider LTSS Concentration
Provider LTSS Concentration = 
DIVIDE(
    [LTSS Total Cost],
    [Total Cost],
    0
)

// Provider Efficiency Score (Cost per Unit)
Provider Efficiency Score = 
DIVIDE(
    [Total Cost],
    SUM(authorization_data[Approved Units]),
    0
)

// Provider Growth Rate (YOY using provider_data)
Provider Member Growth Rate = 
VAR CurrentYearMembers = 
    CALCULATE(
        SUM(provider_data[Member Count]),
        YEAR(Calendar_Table[Date]) = YEAR(TODAY())
    )
VAR PreviousYearMembers = 
    CALCULATE(
        SUM(provider_data[Member Count]),
        YEAR(Calendar_Table[Date]) = YEAR(TODAY()) - 1
    )
RETURN
DIVIDE(
    CurrentYearMembers - PreviousYearMembers,
    PreviousYearMembers,
    0
)

// Provider Cost Growth Rate (YOY)
Provider Cost Growth Rate = 
VAR CurrentPeriodCost = [Total Cost]
VAR PreviousPeriodCost = 
    CALCULATE(
        [Total Cost],
        DATEADD(Calendar_Table[Date], -1, YEAR)
    )
RETURN
DIVIDE(
    CurrentPeriodCost - PreviousPeriodCost,
    PreviousPeriodCost,
    0
)
```

### Advanced Analytics Measures (Enhanced with Mapping Table)
```dax
// Member Loyalty Score (months with provider)
Member Loyalty Score = 
AVERAGEX(
    VALUES(authorization_data[Member ID]),
    CALCULATE(DISTINCTCOUNT(authorization_data[Auth Month]))
)

// Cost Variance from Benchmark
Cost Variance = 
VAR ProviderCost = [PMPM]
VAR BenchmarkCost = 
    CALCULATE(
        [PMPM],
        REMOVEFILTERS(provider_data)
    )
RETURN
DIVIDE(
    ProviderCost - BenchmarkCost,
    BenchmarkCost,
    0
)

// Risk-Adjusted PMPM (by member complexity)
Risk Adjusted PMPM = 
VAR MemberComplexity = 
    AVERAGEX(
        VALUES(authorization_data[Member ID]),
        CALCULATE(DISTINCTCOUNT(authorization_data[Procedure Code]))
    )
VAR ComplexityAdjustment = 1 + (MemberComplexity - 3) * 0.1
RETURN
DIVIDE([PMPM], ComplexityAdjustment, 0)

// Enhanced PMPM from both data sources
PMPM = 
DIVIDE(
    [Total Cost],
    DISTINCTCOUNT(authorization_data[Member ID]) * DISTINCTCOUNT(authorization_data[Auth Month])
)

// LTSS PMPM (using mapping table)
LTSS PMPM = 
DIVIDE(
    [LTSS Total Cost],
    DISTINCTCOUNT(authorization_data[Member ID]) * DISTINCTCOUNT(authorization_data[Auth Month])
)

// Service Mix Analysis
LTSS Service Mix = 
CALCULATE(
    DISTINCTCOUNT(ltss_procedure_mapping[LTSS_Category]),
    RELATED(ltss_procedure_mapping[IS_LTSS]) = "Yes"
)

// Average Units per LTSS Category
Avg Units per LTSS Category = 
AVERAGEX(
    VALUES(ltss_procedure_mapping[LTSS_Category]),
    CALCULATE(
        SUM(authorization_data[Approved Units]),
        RELATED(ltss_procedure_mapping[IS_LTSS]) = "Yes"
    )
)

// Top LTSS Category by Cost
Top LTSS Category Cost = 
CALCULATE(
    MAX(authorization_data[Total Cost]),
    RELATED(ltss_procedure_mapping[IS_LTSS]) = "Yes"
)
```

## 📈 Dashboard Page Layout

### Page 1: Executive Summary
- **KPI Cards**: Total Members, Total Cost, LTSS Penetration Rate, YOY Growth
- **Trend Charts**: Member growth, Cost trends, LTSS vs Non-LTSS trends
- **Geographic Map**: Provider distribution and performance by region

### Page 2: Provider Performance
- **Matrix Table**: Top 20 providers by cost, member count, efficiency
- **Scatter Plot**: Cost vs Quality metrics
- **Bar Charts**: Provider specialty comparison, Entity type analysis
- **Slicer Panel**: Provider filters (Type, Specialty, Status, Region)

### Page 3: LTSS Deep Dive (Enhanced)
- **Donut Chart**: LTSS vs Non-LTSS cost distribution
- **Stacked Bar Chart**: LTSS cost by category (using LTSS_Category field)
- **Line Chart**: LTSS penetration trends over time
- **Matrix Table**: LTSS categories with procedure codes and descriptions
- **Waterfall Chart**: LTSS cost drivers by category
- **Heat Map**: LTSS utilization by provider and LTSS category
- **Tree Map**: Procedure code usage by cost and frequency

### Page 4: Member Analytics
- **Funnel Chart**: Member journey through care levels
- **Cohort Analysis**: Member retention patterns
- **Box Plot**: Member cost distribution by provider
- **Timeline**: Member enrollment and disenrollment patterns

### Page 5: Financial Analytics
- **PMPM Trends**: Overall and by provider segment
- **Cost Concentration**: Pareto analysis of provider costs
- **Budget vs Actual**: Variance analysis
- **Forecasting**: Predictive cost modeling

## 🔒 Security Implementation

### Row-Level Security (RLS) for CSV Data
```dax
// Provider Access Filter (using provider_data table)
Provider RLS = 
LOOKUPVALUE(
    security_UserProvider[Provider ID],
    security_UserProvider[User Email],
    USERPRINCIPALNAME()
) = provider_data[Provider ID]

// Regional Access Filter (using provider organization)
Regional RLS = 
LOOKUPVALUE(
    security_UserRegion[Region],
    security_UserRegion[User Email], 
    USERPRINCIPALNAME()
) = provider_data[Provider Organisation Name]

// Specialist Access Filter (using relationship specialist)
Specialist RLS = 
LOOKUPVALUE(
    security_UserSpecialist[Specialist Name],
    security_UserSpecialist[User Email], 
    USERPRINCIPALNAME()
) = provider_data[Provider Relationship Specialist Name]
```

## ⚡ Performance Optimization

### Calculated Tables for Aggregations (Updated)
```dax
// Calendar Table (Essential for CSV-based model)
Calendar_Table = 
ADDCOLUMNS(
    CALENDARAUTO(),
    "Year", YEAR([Date]),
    "Month", MONTH([Date]),
    "MonthName", FORMAT([Date], "MMM"),
    "YearMonth", FORMAT([Date], "yyyy-mm"),
    "Quarter", "Q" & ROUNDUP(MONTH([Date])/3,0),
    "YearQuarter", YEAR([Date]) & " Q" & ROUNDUP(MONTH([Date])/3,0)
)

// Monthly Provider Summary (aggregated from all CSV files)
MonthlyProviderSummary = 
SUMMARIZECOLUMNS(
    provider_data[Provider ID],
    provider_data[Provider Name],
    provider_data[Auth Year Month],
    "Provider Member Count", SUM(provider_data[Member Count]),
    "Authorization Total Cost", 
        CALCULATE(
            SUM(authorization_data[Total Cost]),
            USERELATIONSHIP(provider_data[Provider ID], authorization_data[Provider ID])
        ),
    "LTSS Cost", 
        CALCULATE(
            SUM(authorization_data[Total Cost]),
            RELATED(ltss_procedure_mapping[IS_LTSS]) = "Yes"
        ),
    "Non-LTSS Cost", 
        CALCULATE(
            SUM(authorization_data[Total Cost]),
            RELATED(ltss_procedure_mapping[IS_LTSS]) = "No"
        ),
    "Authorization Count", 
        CALCULATE(
            COUNTROWS(authorization_data),
            USERELATIONSHIP(provider_data[Provider ID], authorization_data[Provider ID])
        ),
    "LTSS Authorization Count", 
        CALCULATE(
            COUNTROWS(authorization_data),
            RELATED(ltss_procedure_mapping[IS_LTSS]) = "Yes"
        ),
    "Unique Auth Members", 
        CALCULATE(
            DISTINCTCOUNT(authorization_data[Member ID]),
            USERELATIONSHIP(provider_data[Provider ID], authorization_data[Provider ID])
        )
)

// Provider Hierarchy for Drill-down (from provider_data CSV)
ProviderHierarchy = 
SUMMARIZECOLUMNS(
    provider_data[Organisation Type],
    provider_data[Provider Type], 
    provider_data[Provider Specialty],
    provider_data[Provider ID],
    provider_data[Provider Name],
    "Total Member Count", SUM(provider_data[Member Count]),
    "Relationship Specialist", MAX(provider_data[Provider Relationship Specialist Name])
)

// LTSS Summary by Category
LTSS_CategorySummary = 
SUMMARIZECOLUMNS(
    ltss_procedure_mapping[LTSS_Category],
    ltss_procedure_mapping[IS_LTSS],
    "Total LTSS Cost", 
        CALCULATE(
            SUM(authorization_data[Total Cost]),
            ltss_procedure_mapping[IS_LTSS] = "Yes"
        ),
    "Total LTSS Units", 
        CALCULATE(
            SUM(authorization_data[Approved Units]),
            ltss_procedure_mapping[IS_LTSS] = "Yes"
        ),
    "LTSS Authorization Count", 
        CALCULATE(
            COUNTROWS(authorization_data),
            ltss_procedure_mapping[IS_LTSS] = "Yes"
        ),
    "Unique LTSS Members", 
        CALCULATE(
            DISTINCTCOUNT(authorization_data[Member ID]),
            ltss_procedure_mapping[IS_LTSS] = "Yes"
        ),
    "Procedure Count", COUNTROWS(ltss_procedure_mapping)
)

// Procedure Code Summary
ProcedureCodeSummary = 
SUMMARIZECOLUMNS(
    ltss_procedure_mapping[Procedure Code],
    ltss_procedure_mapping[Procedure Description],
    ltss_procedure_mapping[IS_LTSS],
    ltss_procedure_mapping[LTSS_Category],
    "Usage Count", COUNTROWS(authorization_data),
    "Total Cost", SUM(authorization_data[Total Cost]),
    "Total Units", SUM(authorization_data[Approved Units]),
    "Unique Members", DISTINCTCOUNT(authorization_data[Member ID])
)
```

## 🚀 CSV-Optimized Deployment Strategy

### File Management & Data Refresh
1. **CSV File Location**: Establish consistent file path/SharePoint location
2. **File Naming Convention**: Use standardized naming (e.g., provider_data_YYYYMMDD.csv)
3. **Data Refresh**: Schedule based on CSV update frequency
4. **Data Validation**: Implement data quality checks for CSV imports

### CSV-Specific Performance Optimization
- **Data Types**: Optimize column data types during CSV import
- **Compression**: Use Power BI's built-in compression for imported CSV data
- **Incremental Refresh**: Not applicable for CSV files - use full refresh
- **File Size Management**: Monitor CSV file sizes and split if needed (>100MB)

### Change Management for CSV Updates
- **Version Control**: Track CSV file versions and changes
- **Schema Changes**: Document and communicate CSV structure modifications
- **Backup Strategy**: Maintain historical CSV files for rollback capability
- **Data Lineage**: Document CSV source systems and transformation logic

## 📋 Implementation Checklist

### Phase 1: CSV Import & Setup (Weeks 1-2)
- [ ] Import provider_data.csv, authorization_data.csv, and ltss_procedure_mapping.csv
- [ ] Create Calendar_Table calculated table
- [ ] Establish relationships between all CSV tables
- [ ] Set up proper data types and formatting
- [ ] Validate procedure code mapping completeness
- [ ] Create calculated columns using RELATED() functions
- [ ] Implement basic DAX measures

### Phase 2: Enhancement (Weeks 3-4)  
- [ ] Add calculated columns (Is LTSS, LTSS Category, Procedure Description)
- [ ] Create calculated tables for aggregations (including LTSS category summaries)
- [ ] Implement advanced analytics measures with mapping table logic
- [ ] Build provider hierarchy and LTSS category hierarchy for drill-downs
- [ ] Performance tune the imported data model
- [ ] Validate LTSS categorization accuracy

### Phase 3: Visualization & Security (Weeks 5-6)
- [ ] Build all dashboard pages with visualizations
- [ ] Implement RLS if needed
- [ ] Create parameter tables for dynamic filtering
- [ ] UAT and feedback incorporation
- [ ] Optimize for CSV-based refresh patterns

### Phase 4: Deployment & Training (Weeks 7-8)
- [ ] Production deployment to Power BI Service
- [ ] Set up scheduled refresh for CSV files
- [ ] User training delivery focusing on CSV limitations
- [ ] Go-live support and CSV update procedures

## 🎯 Success Metrics

### Technical KPIs
- **Query Performance**: <3 second response time for standard reports
- **Refresh Success**: >99% successful scheduled refreshes
- **User Adoption**: >80% monthly active users
- **Data Accuracy**: <0.1% variance from source systems

### Business KPIs  
- **Provider Insights**: Monthly provider performance reviews
- **Cost Management**: 5% reduction in unnecessary LTSS authorizations
- **Member Outcomes**: Improved member satisfaction scores
- **Operational Efficiency**: 25