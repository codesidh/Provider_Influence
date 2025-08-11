#!/usr/bin/env python3
"""
Power BI Report Generator for Provider Influence Dashboard
Based on Enterprise Implementation Guide
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json

def create_calendar_table():
    """Create a comprehensive calendar table for Power BI"""
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 12, 31)
    date_range = pd.date_range(start=start_date, end=end_date, freq='D')
    
    calendar_data = []
    for date in date_range:
        calendar_data.append({
            'Date': date,
            'Year': date.year,
            'Month': date.month,
            'MonthName': date.strftime('%b'),
            'YearMonth': date.strftime('%Y-%m'),
            'Quarter': f"Q{(date.month-1)//3 + 1}",
            'YearQuarter': f"{date.year} Q{(date.month-1)//3 + 1}",
            'DayOfWeek': date.strftime('%A'),
            'DayOfWeekNum': date.weekday(),
            'WeekOfYear': date.isocalendar()[1],
            'IsWeekend': 1 if date.weekday() >= 5 else 0,
            'IsMonthEnd': 1 if date.month != (date + timedelta(days=1)).month else 0
        })
    
    return pd.DataFrame(calendar_data)

def create_enhanced_provider_data():
    """Create enhanced provider data with calculated fields"""
    # Read original provider data
    provider_df = pd.read_csv('data/provider_data.csv')
    
    # Add calculated columns
    provider_df['Auth Year Month Date'] = pd.to_datetime(provider_df['Auth Year Month'] + '-01')
    provider_df['Year'] = provider_df['Auth Year Month Date'].dt.year
    provider_df['Month'] = provider_df['Auth Year Month Date'].dt.month
    
    return provider_df

def create_enhanced_authorization_data():
    """Create enhanced authorization data with calculated fields"""
    # Read original authorization data
    auth_df = pd.read_csv('data/authorization_data.csv')
    
    # Add calculated columns
    auth_df['Auth Month Date'] = pd.to_datetime(auth_df['Auth Month'] + '-01')
    auth_df['Year'] = auth_df['Auth Month Date'].dt.year
    auth_df['Month'] = auth_df['Auth Month Date'].dt.month
    
    return auth_df

def create_ltss_summary():
    """Create LTSS summary data"""
    ltss_df = pd.read_csv('data/ltss_procedure_mapping.csv')
    auth_df = pd.read_csv('data/authorization_data.csv')
    
    # Merge to get LTSS information
    merged_df = auth_df.merge(ltss_df, on='Procedure Code', how='left')
    
    # Create LTSS summary by category
    ltss_summary = merged_df[merged_df['IS_LTSS'] == 'Yes'].groupby('LTSS_Category').agg({
        'Total Cost': 'sum',
        'Approved Units': 'sum',
        'Member ID': 'nunique',
        'Procedure Code': 'nunique'
    }).reset_index()
    
    ltss_summary.columns = ['LTSS_Category', 'Total_LTSS_Cost', 'Total_LTSS_Units', 'Unique_Members', 'Procedure_Count']
    
    return ltss_summary

def create_provider_summary():
    """Create provider summary table"""
    provider_df = pd.read_csv('data/provider_data.csv')
    auth_df = pd.read_csv('data/authorization_data.csv')
    ltss_df = pd.read_csv('data/ltss_procedure_mapping.csv')
    
    # Merge all data
    merged_df = auth_df.merge(ltss_df, on='Procedure Code', how='left')
    
    # Create provider summary
    provider_summary = merged_df.groupby('Provider ID').agg({
        'Total Cost': 'sum',
        'Approved Units': 'sum',
        'Member ID': 'nunique',
        'Procedure Code': 'nunique'
    }).reset_index()
    
    # Add LTSS specific metrics
    ltss_metrics = merged_df[merged_df['IS_LTSS'] == 'Yes'].groupby('Provider ID').agg({
        'Total Cost': 'sum',
        'Approved Units': 'sum',
        'Member ID': 'nunique'
    }).reset_index()
    
    ltss_metrics.columns = ['Provider ID', 'LTSS_Total_Cost', 'LTSS_Total_Units', 'LTSS_Unique_Members']
    
    # Merge with provider data
    final_summary = provider_summary.merge(ltss_metrics, on='Provider ID', how='left')
    final_summary = final_summary.merge(
        provider_df[['Provider ID', 'Provider Name', 'Provider Type', 'Provider Specialty', 'Provider Status']].drop_duplicates(),
        on='Provider ID',
        how='left'
    )
    
    # Fill NaN values
    final_summary = final_summary.fillna(0)
    
    # Add calculated metrics
    final_summary['LTSS_Cost_Share'] = np.where(
        final_summary['Total Cost'] > 0,
        final_summary['LTSS_Total_Cost'] / final_summary['Total Cost'],
        0
    )
    
    final_summary['Cost_per_Unit'] = np.where(
        final_summary['Approved Units'] > 0,
        final_summary['Total Cost'] / final_summary['Approved Units'],
        0
    )
    
    return final_summary

def create_member_analytics():
    """Create member analytics table"""
    auth_df = pd.read_csv('data/authorization_data.csv')
    ltss_df = pd.read_csv('data/ltss_procedure_mapping.csv')
    
    # Merge to get LTSS information
    merged_df = auth_df.merge(ltss_df, on='Procedure Code', how='left')
    
    # Create member summary
    member_summary = merged_df.groupby('Member ID').agg({
        'Total Cost': 'sum',
        'Approved Units': 'sum',
        'Provider ID': 'nunique',
        'Procedure Code': 'nunique',
        'Auth Month': 'nunique'
    }).reset_index()
    
    # Add LTSS specific metrics
    ltss_member_metrics = merged_df[merged_df['IS_LTSS'] == 'Yes'].groupby('Member ID').agg({
        'Total Cost': 'sum',
        'Approved Units': 'sum',
        'Procedure Code': 'nunique'
    }).reset_index()
    
    ltss_member_metrics.columns = ['Member ID', 'LTSS_Total_Cost', 'LTSS_Total_Units', 'LTSS_Procedure_Count']
    
    # Merge
    final_member_summary = member_summary.merge(ltss_member_metrics, on='Member ID', how='left')
    final_member_summary = final_member_summary.fillna(0)
    
    # Add calculated metrics
    final_member_summary['LTSS_Cost_Share'] = np.where(
        final_member_summary['Total Cost'] > 0,
        final_member_summary['LTSS_Total_Cost'] / final_member_summary['Total Cost'],
        0
    )
    
    final_member_summary['Cost_per_Month'] = np.where(
        final_member_summary['Auth Month'] > 0,
        final_member_summary['Total Cost'] / final_member_summary['Auth Month'],
        0
    )
    
    return final_member_summary

def create_dax_measures():
    """Generate DAX measures for Power BI"""
    dax_measures = {
        "Core_Metrics": {
            "Total_Members": "DISTINCTCOUNT(authorization_data[Member ID])",
            "Total_Cost": "SUM(authorization_data[Total Cost])",
            "Total_Units": "SUM(authorization_data[Approved Units])",
            "Total_Authorizations": "COUNTROWS(authorization_data)"
        },
        "LTSS_Metrics": {
            "LTSS_Total_Cost": "CALCULATE(SUM(authorization_data[Total Cost]), RELATED(ltss_procedure_mapping[IS_LTSS]) = \"Yes\")",
            "LTSS_Penetration_Rate": "DIVIDE(CALCULATE(DISTINCTCOUNT(authorization_data[Member ID]), RELATED(ltss_procedure_mapping[IS_LTSS]) = \"Yes\"), [Total_Members], 0)",
            "LTSS_Cost_Share": "DIVIDE([LTSS_Total_Cost], [Total_Cost], 0)",
            "LTSS_Authorization_Count": "CALCULATE(COUNTROWS(authorization_data), RELATED(ltss_procedure_mapping[IS_LTSS]) = \"Yes\")"
        },
        "Provider_Metrics": {
            "Provider_Market_Share": "DIVIDE([Total_Cost], CALCULATE([Total_Cost], REMOVEFILTERS(provider_data)), 0)",
            "Provider_LTSS_Concentration": "DIVIDE([LTSS_Total_Cost], [Total_Cost], 0)",
            "Provider_Efficiency_Score": "DIVIDE([Total_Cost], SUM(authorization_data[Approved Units]), 0)"
        },
        "Financial_Metrics": {
            "PMPM": "DIVIDE([Total_Cost], DISTINCTCOUNT(authorization_data[Member ID]) * DISTINCTCOUNT(authorization_data[Auth Month]), 0)",
            "LTSS_PMPM": "DIVIDE([LTSS_Total_Cost], DISTINCTCOUNT(authorization_data[Member ID]) * DISTINCTCOUNT(authorization_data[Auth Month]), 0)",
            "Cost_per_Unit": "DIVIDE([Total_Cost], [Total_Units], 0)"
        }
    }
    
    return dax_measures

def create_powerbi_report_structure():
    """Create the Power BI report structure"""
    report_structure = {
        "Report_Name": "Provider Influence Power BI Dashboard",
        "Pages": [
            {
                "Page_Name": "Executive Summary",
                "Visualizations": [
                    "KPI Cards: Total Members, Total Cost, LTSS Penetration Rate, YOY Growth",
                    "Trend Charts: Member growth, Cost trends, LTSS vs Non-LTSS trends",
                    "Geographic Map: Provider distribution and performance by region"
                ]
            },
            {
                "Page_Name": "Provider Performance",
                "Visualizations": [
                    "Matrix Table: Top 20 providers by cost, member count, efficiency",
                    "Scatter Plot: Cost vs Quality metrics",
                    "Bar Charts: Provider specialty comparison, Entity type analysis",
                    "Slicer Panel: Provider filters (Type, Specialty, Status, Region)"
                ]
            },
            {
                "Page_Name": "LTSS Deep Dive",
                "Visualizations": [
                    "Donut Chart: LTSS vs Non-LTSS cost distribution",
                    "Stacked Bar Chart: LTSS cost by category",
                    "Line Chart: LTSS penetration trends over time",
                    "Matrix Table: LTSS categories with procedure codes and descriptions",
                    "Waterfall Chart: LTSS cost drivers by category",
                    "Heat Map: LTSS utilization by provider and LTSS category"
                ]
            },
            {
                "Page_Name": "Member Analytics",
                "Visualizations": [
                    "Funnel Chart: Member journey through care levels",
                    "Cohort Analysis: Member retention patterns",
                    "Box Plot: Member cost distribution by provider",
                    "Timeline: Member enrollment and disenrollment patterns"
                ]
            },
            {
                "Page_Name": "Financial Analytics",
                "Visualizations": [
                    "PMPM Trends: Overall and by provider segment",
                    "Cost Concentration: Pareto analysis of provider costs",
                    "Budget vs Actual: Variance analysis",
                    "Forecasting: Predictive cost modeling"
                ]
            }
        ],
        "Data_Model": {
            "Tables": [
                "provider_data",
                "authorization_data", 
                "ltss_procedure_mapping",
                "Calendar_Table",
                "Provider_Summary",
                "LTSS_Summary",
                "Member_Analytics"
            ],
            "Relationships": [
                "provider_data[Provider ID] (1) ←→ (*) authorization_data[Provider ID]",
                "Calendar_Table[Date] (1) ←→ (*) authorization_data[Auth Month Date]",
                "Calendar_Table[Date] (1) ←→ (*) provider_data[Auth Year Month Date]",
                "ltss_procedure_mapping[Procedure Code] (1) ←→ (*) authorization_data[Procedure Code]"
            ]
        }
    }
    
    return report_structure

def generate_powerbi_files():
    """Generate all necessary files for Power BI implementation"""
    
    print("🚀 Creating Power BI Report Components...")
    
    # Create enhanced data tables
    print("📊 Creating enhanced data tables...")
    
    # Calendar table
    calendar_df = create_calendar_table()
    calendar_df.to_csv('data/Calendar_Table.csv', index=False)
    print("✅ Calendar table created")
    
    # Enhanced provider data
    enhanced_provider_df = create_enhanced_provider_data()
    enhanced_provider_df.to_csv('data/Enhanced_Provider_Data.csv', index=False)
    print("✅ Enhanced provider data created")
    
    # Enhanced authorization data
    enhanced_auth_df = create_enhanced_authorization_data()
    enhanced_auth_df.to_csv('data/Enhanced_Authorization_Data.csv', index=False)
    print("✅ Enhanced authorization data created")
    
    # LTSS summary
    ltss_summary_df = create_ltss_summary()
    ltss_summary_df.to_csv('data/LTSS_Summary.csv', index=False)
    print("✅ LTSS summary created")
    
    # Provider summary
    provider_summary_df = create_provider_summary()
    provider_summary_df.to_csv('data/Provider_Summary.csv', index=False)
    print("✅ Provider summary created")
    
    # Member analytics
    member_analytics_df = create_member_analytics()
    member_analytics_df.to_csv('data/Member_Analytics.csv', index=False)
    print("✅ Member analytics created")
    
    # Generate DAX measures
    print("🧮 Generating DAX measures...")
    dax_measures = create_dax_measures()
    
    with open('data/DAX_Measures.json', 'w') as f:
        json.dump(dax_measures, f, indent=2)
    print("✅ DAX measures created")
    
    # Generate report structure
    print("📋 Creating report structure...")
    report_structure = create_powerbi_report_structure()
    
    with open('data/Report_Structure.json', 'w') as f:
        json.dump(report_structure, f, indent=2)
    print("✅ Report structure created")
    
    # Create implementation guide
    print("📚 Creating implementation guide...")
    create_implementation_guide()
    print("✅ Implementation guide created")
    
    print("\n🎉 Power BI Report Components Generated Successfully!")
    print("\n📁 Files created in 'data/' directory:")
    print("   • Calendar_Table.csv")
    print("   • Enhanced_Provider_Data.csv") 
    print("   • Enhanced_Authorization_Data.csv")
    print("   • LTSS_Summary.csv")
    print("   • Provider_Summary.csv")
    print("   • Member_Analytics.csv")
    print("   • DAX_Measures.json")
    print("   • Report_Structure.json")
    print("   • PowerBI_Implementation_Guide.md")
    
    print("\n🚀 Next Steps:")
    print("   1. Open Power BI Desktop")
    print("   2. Import all CSV files from the 'data/' directory")
    print("   3. Create relationships as specified in Report_Structure.json")
    print("   4. Add DAX measures from DAX_Measures.json")
    print("   5. Build visualizations following the dashboard layout")
    print("   6. Follow the implementation guide for best practices")

def create_implementation_guide():
    """Create a comprehensive implementation guide"""
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    guide_content = f"""# Power BI Implementation Guide - Provider Influence Dashboard

## Quick Start Guide

### 1. Import Data Sources
1. Open Power BI Desktop
2. Click "Get Data" -> "Text/CSV"
3. Import the following files in order:
   - Calendar_Table.csv
   - provider_data.csv
   - authorization_data.csv
   - ltss_procedure_mapping.csv
   - Enhanced_Provider_Data.csv
   - Enhanced_Authorization_Data.csv
   - LTSS_Summary.csv
   - Provider_Summary.csv
   - Member_Analytics.csv

### 2. Set Up Data Model Relationships
Create the following relationships in Power BI:

provider_data[Provider ID] (1) <-> (*) authorization_data[Provider ID]
Calendar_Table[Date] (1) <-> (*) authorization_data[Auth Month Date]
Calendar_Table[Date] (1) <-> (*) provider_data[Auth Year Month Date]
ltss_procedure_mapping[Procedure Code] (1) <-> (*) authorization_data[Procedure Code]

### 3. Add Calculated Columns
Add these calculated columns to the authorization_data table:

Is LTSS = 
SWITCH(
    TRUE(),
    authorization_data[Procedure Code] IN {{"T1019", "S5125", "T2025", "S5150", "S5151"}}, "LTSS",
    authorization_data[Procedure Code] IN {{"99401", "99402"}}, "Preventive",
    "Non-LTSS"
)

LTSS Category = 
LOOKUPVALUE(
    ltss_procedure_mapping[LTSS_Category],
    ltss_procedure_mapping[Procedure Code],
    authorization_data[Procedure Code]
)

### 4. Add DAX Measures
Copy the measures from DAX_Measures.json into your Power BI model.

### 5. Build Dashboard Pages
Follow the structure in Report_Structure.json to create your 5 dashboard pages.

## Key Visualizations by Page

### Page 1: Executive Summary
- KPI Cards: Use card visuals with the core DAX measures
- Trend Charts: Line charts showing monthly trends
- Geographic Map: Map visual (if you have location data)

### Page 2: Provider Performance  
- Matrix Table: Table visual with provider metrics
- Scatter Plot: Scatter chart with cost vs efficiency
- Bar Charts: Column charts for comparisons

### Page 3: LTSS Deep Dive
- Donut Chart: Pie chart for LTSS distribution
- Stacked Bar: Column chart with LTSS categories
- Heat Map: Matrix visual for provider vs LTSS category

### Page 4: Member Analytics
- Funnel Chart: Funnel visual for member journey
- Cohort Analysis: Matrix visual for retention
- Box Plot: Box and whisker for cost distribution

### Page 5: Financial Analytics
- PMPM Trends: Line chart with time series
- Pareto Chart: Column chart with cumulative line
- Forecasting: Line chart with trend lines

## Performance Optimization Tips

1. Data Types: Ensure proper data types are set
2. Relationships: Verify all relationships are correct
3. Measures: Use calculated columns sparingly, prefer measures
4. Filters: Apply filters at the page level when possible
5. Refresh: Test data refresh process

## Publishing to Power BI Service

1. Click "Publish" in Power BI Desktop
2. Select your Power BI workspace
3. Set up scheduled refresh for data sources
4. Configure row-level security if needed
5. Share with stakeholders

## Success Metrics

- Query Performance: <3 second response time
- User Adoption: >80% monthly active users  
- Data Accuracy: <0.1% variance from source
- Refresh Success: >99% successful scheduled refreshes

## Troubleshooting

### Common Issues:
1. Relationship Errors: Check data types and cardinality
2. Performance Issues: Review DAX measures and relationships
3. Refresh Failures: Verify file paths and permissions
4. Visual Errors: Check for missing relationships or data

### Support Resources:
- Power BI Community Forums
- Microsoft Power BI Documentation
- DAX Studio for measure optimization

## Contact Information

For technical support or questions about this implementation:
- Review the enterprise implementation guide
- Check the DAX measures documentation
- Validate data relationships and cardinality

---
Generated on: {current_time}
Provider Influence Power BI Dashboard Implementation Guide
"""
    
    with open('data/PowerBI_Implementation_Guide.md', 'w', encoding='utf-8') as f:
        f.write(guide_content)

if __name__ == "__main__":
    generate_powerbi_files()
