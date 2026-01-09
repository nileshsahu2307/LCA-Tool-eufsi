# Product Requirements Document (PRD)
## EUFSI LCA Tool - Feature Enhancements

**Version**: 1.0
**Date**: 2026-01-08
**Based on**: Earthster LCA Tool Analysis
**Product**: EUFSI LCA Tool
**Status**: Draft for Review

---

## Executive Summary

This PRD outlines feature enhancements for the EUFSI LCA Tool based on analysis of Earthster's T-shirt LCA platform. The goal is to improve user experience, expand functionality, and provide comprehensive lifecycle assessment capabilities for fashion/textile products.

### Key Enhancement Areas:
1. **Release Management System** - Version control for LCA assessments
2. **Advanced Data Visualization** - Interactive charts and impact breakdowns
3. **Data Source Management** - Transparent data provenance tracking
4. **Export & Reporting** - Professional PDF/Excel report generation
5. **Review & Collaboration** - Multi-user review workflows
6. **Impact Categories** - Expanded environmental metrics
7. **Geographic Specificity** - Region-based calculations
8. **Unit Scaling** - Flexible calculation units

---

## Problem Statement

### Current State (EUFSI LCA Tool):
- Basic project and activity management
- Simple calculation interface
- Limited visualization capabilities
- No version control or release management
- Basic export functionality
- Single impact assessment view

### Desired State:
- Professional LCA platform comparable to Earthster
- Comprehensive impact visualization
- Transparent data source management
- Version-controlled releases
- Collaborative review workflows
- Advanced reporting and export options
- Multi-category impact assessment

### Gap Analysis:
| Feature | Current | Desired | Priority |
|---------|---------|---------|----------|
| Release Management | ❌ None | ✅ Full versioning | P0 |
| Impact Visualization | ⚠️ Basic | ✅ Interactive charts | P0 |
| Data Sources | ❌ None | ✅ Tracked & cited | P1 |
| Export/Reports | ⚠️ Basic | ✅ Professional PDFs | P0 |
| Review Workflow | ❌ None | ✅ Multi-user review | P2 |
| Impact Categories | ⚠️ Limited | ✅ 6+ categories | P0 |
| Geographic Data | ❌ None | ✅ Region-specific | P1 |
| Unit Scaling | ⚠️ Fixed | ✅ Flexible units | P1 |

---

## Target Users

### Primary Users:
1. **Sustainability Analysts** - Conduct detailed LCA assessments
2. **Fashion Brands** - Assess product environmental impact
3. **Supply Chain Managers** - Track manufacturing impacts
4. **Compliance Officers** - Generate regulatory reports

### Secondary Users:
1. **Researchers** - Academic LCA studies
2. **Consultants** - Client LCA services
3. **Manufacturers** - Product optimization

### User Personas:

#### Persona 1: Sarah - Sustainability Manager at Fashion Brand
- **Goal**: Assess 100 T-shirt SKUs for sustainability report
- **Pain Points**: Needs batch processing, comparative analysis, professional reports
- **Technical Level**: Medium
- **Frequency**: Weekly assessments

#### Persona 2: Dr. James - Academic Researcher
- **Goal**: Conduct detailed LCA studies for publication
- **Pain Points**: Needs data transparency, citation management, peer review
- **Technical Level**: High
- **Frequency**: Monthly deep-dive assessments

#### Persona 3: Maria - Compliance Officer
- **Goal**: Generate regulatory compliance reports
- **Pain Points**: Needs standardized formats, audit trails, version control
- **Technical Level**: Low-Medium
- **Frequency**: Quarterly reports

---

## Feature Requirements

## 1. Release Management System (P0)

### Overview
Implement version control for LCA projects, allowing users to create releases, track changes, and maintain historical records.

### User Stories
**As a** sustainability analyst
**I want to** create versioned releases of my LCA assessments
**So that** I can track changes over time and compare different versions

**As a** compliance officer
**I want to** lock completed assessments as releases
**So that** I have an audit trail for regulatory reporting

### Functional Requirements

#### 1.1 Release Creation
- **FR-1.1.1**: Users can create a new release from any project
- **FR-1.1.2**: Release requires a name, version number, and optional description
- **FR-1.1.3**: Release captures complete snapshot of project data at creation time
- **FR-1.1.4**: System auto-generates release ID and timestamp
- **FR-1.1.5**: Users can tag releases (e.g., "Draft", "Final", "Submitted", "Published")

#### 1.2 Release Management
- **FR-1.2.1**: View list of all releases for a project
- **FR-1.2.2**: Compare two releases side-by-side
- **FR-1.2.3**: Restore project to a previous release state
- **FR-1.2.4**: Delete releases (with confirmation)
- **FR-1.2.5**: Export specific release data

#### 1.3 Release Metadata
- **FR-1.3.1**: Release creator name and timestamp
- **FR-1.3.2**: Release notes (markdown support)
- **FR-1.3.3**: Change log (what changed from previous release)
- **FR-1.3.4**: Lock status (locked releases cannot be modified)
- **FR-1.3.5**: Associated data sources and versions

### Technical Requirements
- **TR-1.1**: Store release data as separate collection in MongoDB
- **TR-1.2**: Implement snapshot mechanism (deep copy of project data)
- **TR-1.3**: Use semantic versioning (major.minor.patch)
- **TR-1.4**: API endpoint: `POST /api/projects/{id}/releases`
- **TR-1.5**: API endpoint: `GET /api/projects/{id}/releases`
- **TR-1.6**: API endpoint: `GET /api/releases/{release_id}`
- **TR-1.7**: Maximum 50 releases per project (configurable)

### UI/UX Requirements
- **UX-1.1**: Add "Releases" tab to project view
- **UX-1.2**: "Create Release" button prominently displayed
- **UX-1.3**: Release list shows version, date, creator, status
- **UX-1.4**: Visual indicator for locked releases (lock icon)
- **UX-1.5**: Timeline view showing release history

### Acceptance Criteria
- [ ] User can create a release with name and description
- [ ] Release captures all project data including activities and calculations
- [ ] User can view list of all releases for a project
- [ ] User can compare two releases and see differences
- [ ] User can export data from a specific release
- [ ] Locked releases cannot be modified
- [ ] Release metadata displays correctly

---

## 2. Advanced Data Visualization (P0)

### Overview
Implement interactive, professional-grade charts showing impact breakdowns across categories, activities, and lifecycle stages.

### User Stories
**As a** sustainability analyst
**I want to** see visual breakdown of environmental impacts
**So that** I can quickly identify hotspots and communicate results

**As a** brand manager
**I want to** compare products visually
**So that** I can make informed decisions about product design

### Functional Requirements

#### 2.1 Impact Breakdown Charts
- **FR-2.1.1**: Pie chart showing percentage contribution by impact category
- **FR-2.1.2**: Bar chart comparing impact categories
- **FR-2.1.3**: Stacked bar chart showing activity contributions
- **FR-2.1.4**: Interactive tooltips showing exact values
- **FR-2.1.5**: Export charts as PNG/SVG

#### 2.2 Impact Categories Visualization
Display six core impact categories:
1. **Water Use** - Liters consumed
2. **Climate Change** - kg CO2 equivalent
3. **Damage to Human Health** - DALY (Disability-Adjusted Life Years)
4. **Damage to Ecosystems** - PDF·m²·year (Potentially Disappeared Fraction)
5. **Damage to Resource Availability** - USD
6. **Other Impacts** - Aggregated secondary impacts

#### 2.3 Comparative Visualization
- **FR-2.3.1**: Compare multiple products side-by-side
- **FR-2.3.2**: Compare different releases of same product
- **FR-2.3.3**: Benchmark against industry averages
- **FR-2.3.4**: Scenario comparison (what-if analysis)

#### 2.4 Dashboard View
- **FR-2.4.1**: Overview dashboard showing key metrics
- **FR-2.4.2**: Trend charts (if multiple assessments exist)
- **FR-2.4.3**: Hotspot identification (automatically highlight highest impacts)
- **FR-2.4.4**: Traffic light indicators (red/yellow/green) for thresholds

### Technical Requirements
- **TR-2.1**: Use Chart.js or Recharts for visualization
- **TR-2.2**: Backend calculates percentage contributions
- **TR-2.3**: API endpoint: `GET /api/projects/{id}/visualizations`
- **TR-2.4**: Support responsive charts (mobile-friendly)
- **TR-2.5**: Implement chart caching for performance
- **TR-2.6**: Color scheme follows accessibility guidelines (WCAG 2.1)

### UI/UX Requirements
- **UX-2.1**: Charts use consistent color scheme:
  - Water Use: Blue (#2196F3)
  - Climate Change: Orange (#FF9800)
  - Human Health: Red (#F44336)
  - Ecosystems: Green (#4CAF50)
  - Resource Availability: Purple (#9C27B0)
  - Other: Gray (#9E9E9E)
- **UX-2.2**: Interactive legend (click to hide/show categories)
- **UX-2.3**: Zoom and pan for detailed exploration
- **UX-2.4**: Print-friendly versions available
- **UX-2.5**: Loading states while calculating

### Acceptance Criteria
- [ ] Pie chart displays impact category breakdown with percentages
- [ ] Bar charts allow comparison between products
- [ ] Charts are interactive with hover tooltips
- [ ] All six impact categories are visualized
- [ ] Charts export to PNG/SVG format
- [ ] Responsive design works on mobile devices
- [ ] Charts follow WCAG 2.1 accessibility guidelines

---

## 3. Data Source Management (P1)

### Overview
Track and cite all data sources used in LCA calculations, providing transparency and credibility.

### User Stories
**As a** researcher
**I want to** cite all data sources used in my assessment
**So that** my work is credible and reproducible

**As a** auditor
**I want to** verify data sources used in calculations
**So that** I can validate the assessment methodology

### Functional Requirements

#### 3.1 Data Source Registration
- **FR-3.1.1**: Register data sources (databases, literature, primary data)
- **FR-3.1.2**: Data source types:
  - Ecoinvent database
  - Industry average data
  - Primary collected data
  - Literature (journal papers, reports)
  - Manufacturer data sheets
  - Custom/proprietary data
- **FR-3.1.3**: Required metadata:
  - Source name
  - Version/date
  - Provider/publisher
  - Geographic scope
  - Technology scope
  - Temporal scope
  - Quality rating (1-5 stars)
  - Access URL/DOI
  - Notes

#### 3.2 Source Linking
- **FR-3.2.1**: Link activities to data sources
- **FR-3.2.2**: Link emission factors to sources
- **FR-3.2.3**: Multiple sources per activity (for transparency)
- **FR-3.2.4**: Visual indicator showing which data has sources

#### 3.3 Source Management
- **FR-3.3.1**: Add "Data Sources" tab to project
- **FR-3.3.2**: List all sources used in project
- **FR-3.3.3**: Search and filter sources
- **FR-3.3.4**: Reuse sources across projects
- **FR-3.3.5**: Bulk import sources from CSV

#### 3.4 Source Citation
- **FR-3.4.1**: Auto-generate bibliography in multiple formats (APA, IEEE, Chicago)
- **FR-3.4.2**: Include citations in exported reports
- **FR-3.4.3**: Export sources as BibTeX for academic papers

### Technical Requirements
- **TR-3.1**: New collection: `data_sources`
- **TR-3.2**: Reference sources in activity documents
- **TR-3.3**: API endpoint: `POST /api/data-sources`
- **TR-3.4**: API endpoint: `GET /api/data-sources?project_id={id}`
- **TR-3.5**: Implement citation formatter library
- **TR-3.6**: Support DOI resolution for automatic metadata

### UI/UX Requirements
- **UX-3.1**: "Data Sources" tab in project navigation
- **UX-3.2**: "Add Source" modal with form
- **UX-3.3**: Source quality displayed as star rating
- **UX-3.4**: Visual indicator on activities showing source linkage
- **UX-3.5**: Quick-add source from activity edit screen
- **UX-3.6**: Source preview card showing key metadata

### Acceptance Criteria
- [ ] User can register new data sources with full metadata
- [ ] User can link activities to data sources
- [ ] Data sources tab shows all sources used in project
- [ ] Source quality rating visible and editable
- [ ] Auto-generated bibliography available in multiple formats
- [ ] Sources export with reports
- [ ] DOI resolution works for automatic metadata fetch

---

## 4. Professional Export & Reporting (P0)

### Overview
Generate professional, branded PDF and Excel reports suitable for stakeholder communication and regulatory submission.

### User Stories
**As a** compliance officer
**I want to** generate professional PDF reports
**So that** I can submit them to regulatory bodies

**As a** brand manager
**I want to** export data to Excel
**So that** I can perform additional analysis and create presentations

### Functional Requirements

#### 4.1 PDF Report Generation
- **FR-4.1.1**: Generate comprehensive PDF report
- **FR-4.1.2**: Report sections:
  1. Cover page with logo and title
  2. Executive summary
  3. Methodology description
  4. System boundaries
  5. Data sources and assumptions
  6. Results by impact category
  7. Visual charts and graphs
  8. Detailed activity breakdown
  9. Sensitivity analysis (optional)
  10. Conclusions and recommendations
  11. Appendix with raw data
  12. Bibliography

#### 4.2 Report Customization
- **FR-4.2.1**: Upload company logo
- **FR-4.2.2**: Customize color scheme
- **FR-4.2.3**: Select which sections to include
- **FR-4.2.4**: Add custom text sections
- **FR-4.2.5**: Choose template (simple, detailed, executive)
- **FR-4.2.6**: Save report templates for reuse

#### 4.3 Excel Export
- **FR-4.3.1**: Export complete project data to Excel
- **FR-4.3.2**: Multiple sheets:
  - Summary
  - Activities
  - Materials
  - Impacts by category
  - Data sources
  - Calculations
- **FR-4.3.3**: Formatted tables with headers
- **FR-4.3.4**: Embedded charts in Excel
- **FR-4.3.5**: Formula preservation for transparency

#### 4.4 Other Export Formats
- **FR-4.4.1**: CSV export (for further analysis)
- **FR-4.4.2**: JSON export (for API integration)
- **FR-4.4.3**: ILCD format (international LCA standard)
- **FR-4.4.4**: SimaPro import format (if applicable)

#### 4.5 Report Sharing
- **FR-4.5.1**: Generate shareable link for reports
- **FR-4.5.2**: Email report as attachment
- **FR-4.5.3**: Save report to project for future access
- **FR-4.5.4**: Version reports with releases

### Technical Requirements
- **TR-4.1**: Use ReportLab (Python) or Puppeteer (Node.js) for PDF generation
- **TR-4.2**: Use openpyxl or xlsxwriter for Excel generation
- **TR-4.3**: Store report templates in database
- **TR-4.4**: API endpoint: `POST /api/projects/{id}/export/pdf`
- **TR-4.5**: API endpoint: `POST /api/projects/{id}/export/excel`
- **TR-4.6**: Background job processing for large reports
- **TR-4.7**: Store generated reports in cloud storage (S3/similar)
- **TR-4.8**: Reports expire after 30 days (configurable)

### UI/UX Requirements
- **UX-4.1**: "Export" tab in project view
- **UX-4.2**: Export wizard with step-by-step options
- **UX-4.3**: Report preview before final generation
- **UX-4.4**: Progress indicator during generation
- **UX-4.5**: Download button once report ready
- **UX-4.6**: Email option with recipient input
- **UX-4.7**: Template gallery for selection

### Acceptance Criteria
- [ ] PDF report generates with all required sections
- [ ] Report includes charts and visualizations
- [ ] Company logo can be uploaded and appears on cover
- [ ] Excel export contains all project data in organized sheets
- [ ] CSV export works for raw data
- [ ] Report generation completes within 30 seconds for typical project
- [ ] Generated reports can be downloaded and shared
- [ ] Report templates can be saved and reused

---

## 5. Review & Collaboration Workflow (P2)

### Overview
Enable multi-user review and approval workflows for quality assurance and team collaboration.

### User Stories
**As a** sustainability analyst
**I want to** submit my assessment for peer review
**So that** the quality and accuracy are verified before publication

**As a** team lead
**I want to** review and approve assessments
**So that** only validated data is released

### Functional Requirements

#### 5.1 Review Workflow
- **FR-5.1.1**: Submit project for review
- **FR-5.1.2**: Assign reviewers (single or multiple)
- **FR-5.1.3**: Review statuses:
  - Draft (in progress)
  - Submitted (awaiting review)
  - Under Review (reviewer assigned)
  - Changes Requested (needs revision)
  - Approved (review complete)
  - Rejected (does not meet standards)
- **FR-5.1.4**: Email notifications for status changes
- **FR-5.1.5**: Review deadline setting and reminders

#### 5.2 Commenting System
- **FR-5.2.1**: Add comments to specific activities
- **FR-5.2.2**: Add general comments to project
- **FR-5.2.3**: Reply to comments (threaded)
- **FR-5.2.4**: Resolve comments when addressed
- **FR-5.2.5**: @mention other users
- **FR-5.2.6**: Comment history and audit trail

#### 5.3 Reviewer Tools
- **FR-5.3.1**: Reviewer dashboard showing pending reviews
- **FR-5.3.2**: Side-by-side comparison with previous version
- **FR-5.3.3**: Highlight changes since last review
- **FR-5.3.4**: Checklist of review criteria
- **FR-5.3.5**: Approve/reject buttons with required comments
- **FR-5.3.6**: Request specific changes

#### 5.4 Collaboration Features
- **FR-5.4.1**: Real-time presence indicators (who's viewing)
- **FR-5.4.2**: Activity feed showing recent changes
- **FR-5.4.3**: Share project with team members (read/write/admin permissions)
- **FR-5.4.4**: Lock editing when under review
- **FR-5.4.5**: Version comparison tool

### Technical Requirements
- **TR-5.1**: Implement review status field in project schema
- **TR-5.2**: New collection: `comments`
- **TR-5.3**: New collection: `review_assignments`
- **TR-5.4**: WebSocket for real-time updates
- **TR-5.5**: Email notification service integration
- **TR-5.6**: Permission system (read/write/admin)
- **TR-5.7**: API endpoints for review workflow
- **TR-5.8**: Activity logging for audit trail

### UI/UX Requirements
- **UX-5.1**: "Review" tab in project navigation
- **UX-5.2**: Submit for review button with modal
- **UX-5.3**: Review status badge on project card
- **UX-5.4**: Comment panel (sidebar or modal)
- **UX-5.5**: Reviewer dashboard (separate page)
- **UX-5.6**: Visual indicators for unresolved comments
- **UX-5.7**: Notification bell in header
- **UX-5.8**: Activity timeline view

### Acceptance Criteria
- [ ] User can submit project for review
- [ ] Reviewer receives email notification
- [ ] Reviewer can add comments to activities
- [ ] Reviewer can approve or request changes
- [ ] Submitter receives notification of review status
- [ ] Comments can be resolved
- [ ] Review history is preserved
- [ ] Real-time presence indicators work
- [ ] Permissions system prevents unauthorized edits

---

## 6. Enhanced Impact Categories (P0)

### Overview
Expand from basic carbon footprint to comprehensive environmental impact assessment across six key categories.

### User Stories
**As a** sustainability analyst
**I want to** assess multiple environmental impact categories
**So that** I have a complete picture beyond just carbon emissions

### Functional Requirements

#### 6.1 Core Impact Categories

##### 6.1.1 Water Use
- **Metric**: Liters (L) or cubic meters (m³)
- **Includes**:
  - Freshwater consumption
  - Water withdrawal
  - Water stress index consideration
- **Data needed**: Water consumption per process/activity

##### 6.1.2 Climate Change
- **Metric**: kg CO2 equivalent
- **Includes**:
  - CO2, CH4, N2O, F-gases
  - GWP100 characterization factors
  - Scope 1, 2, 3 emissions
- **Data needed**: GHG emissions by type

##### 6.1.3 Damage to Human Health
- **Metric**: DALY (Disability-Adjusted Life Years)
- **Includes**:
  - Respiratory effects
  - Carcinogenic effects
  - Ionizing radiation
  - Ozone depletion
  - Photochemical oxidation
- **Data needed**: Toxic substance emissions

##### 6.1.4 Damage to Ecosystems
- **Metric**: PDF·m²·year (Potentially Disappeared Fraction)
- **Includes**:
  - Terrestrial ecotoxicity
  - Aquatic ecotoxicity
  - Terrestrial acidification/nutrification
  - Land use impacts
- **Data needed**: Land use, emissions to soil/water

##### 6.1.5 Damage to Resource Availability
- **Metric**: USD (economic value)
- **Includes**:
  - Fossil fuel depletion
  - Mineral resource depletion
  - Energy consumption (primary energy)
- **Data needed**: Resource extraction quantities

##### 6.1.6 Other Impacts
- **Metric**: Various
- **Includes**:
  - Eutrophication
  - Particulate matter formation
  - Ionizing radiation
  - Land use
  - Any other secondary indicators

#### 6.2 Calculation Methods
- **FR-6.2.1**: Support multiple LCIA methods:
  - ReCiPe 2016
  - IMPACT 2002+
  - EcoIndicator 99
  - CML-IA baseline
  - TRACI 2.1
- **FR-6.2.2**: Allow user to select preferred method
- **FR-6.2.3**: Display method metadata and assumptions
- **FR-6.2.4**: Compare results across methods

#### 6.3 Impact Calculation
- **FR-6.3.1**: Calculate all six categories simultaneously
- **FR-6.3.2**: Show contribution analysis (which activities contribute most)
- **FR-6.3.3**: Normalize results (show relative importance)
- **FR-6.3.4**: Weight categories (optional, user-defined)
- **FR-6.3.5**: Calculate single score (if weighted)

#### 6.4 Data Requirements
- **FR-6.4.1**: Emission factors database for all impact categories
- **FR-6.4.2**: Characterization factors for each method
- **FR-6.4.3**: Activity input fields for relevant flows
- **FR-6.4.4**: Validation of input data completeness

### Technical Requirements
- **TR-6.1**: Database of characterization factors
- **TR-6.2**: Calculation engine supporting multiple methods
- **TR-6.3**: Store impact results by category in database
- **TR-6.4**: API endpoint: `GET /api/impact-methods`
- **TR-6.5**: API endpoint: `POST /api/projects/{id}/calculate-impacts`
- **TR-6.6**: Cache calculation results for performance
- **TR-6.7**: Background job for intensive calculations

### UI/UX Requirements
- **UX-6.1**: Impact category selection in project settings
- **UX-6.2**: Visual representation of all six categories
- **UX-6.3**: Toggle between normalized and absolute values
- **UX-6.4**: Explanation tooltips for each category
- **UX-6.5**: Method selection dropdown with descriptions
- **UX-6.6**: Warning if data incomplete for certain categories

### Acceptance Criteria
- [ ] All six impact categories calculate correctly
- [ ] Results display for each category with appropriate units
- [ ] User can select LCIA method
- [ ] Contribution analysis shows which activities contribute most
- [ ] Normalized results available
- [ ] Visual charts show all categories
- [ ] Export includes all impact categories

---

## 7. Geographic Specificity (P1)

### Overview
Enable region-specific calculations accounting for local energy grids, transportation, and environmental conditions.

### User Stories
**As a** sustainability analyst
**I want to** specify geographic regions for activities
**So that** calculations reflect local conditions (e.g., energy grid carbon intensity)

### Functional Requirements

#### 7.1 Geographic Selection
- **FR-7.1.1**: Select country/region for each activity
- **FR-7.1.2**: Supported regions:
  - Europe (by country)
  - North America (US, Canada, Mexico)
  - Asia (China, India, Japan, Southeast Asia)
  - Latin America
  - Africa
  - Oceania
- **FR-7.1.3**: Display flag/icon for selected region
- **FR-7.1.4**: Default to project-level geography (can override per activity)

#### 7.2 Region-Specific Data
- **FR-7.2.1**: Electricity grid carbon intensity by region
- **FR-7.2.2**: Transportation distances and modes by region
- **FR-7.2.3**: Water stress indices by region
- **FR-7.2.4**: Waste treatment methods by region
- **FR-7.2.5**: Regulatory limits and standards by region

#### 7.3 Geographic Calculations
- **FR-7.3.1**: Adjust emission factors based on geography
- **FR-7.3.2**: Calculate transportation impacts based on origin-destination
- **FR-7.3.3**: Weight water use by regional water scarcity
- **FR-7.3.4**: Show geographic breakdown in results

#### 7.4 Multi-Region Products
- **FR-7.4.1**: Support supply chains spanning multiple regions
- **FR-7.4.2**: Track material origin, manufacturing location, use location
- **FR-7.4.3**: Visualize supply chain on map
- **FR-7.4.4**: Calculate transportation between regions

### Technical Requirements
- **TR-7.1**: Database of regional factors (grid carbon, water stress, etc.)
- **TR-7.2**: Geographic field in activity schema
- **TR-7.3**: Calculation logic considering geographic factors
- **TR-7.4**: API endpoint: `GET /api/geographic-data`
- **TR-7.5**: Integration with mapping library (Leaflet or Mapbox)
- **TR-7.6**: Distance calculation between regions

### UI/UX Requirements
- **UX-7.1**: Country/region dropdown with flag icons
- **UX-7.2**: Map view showing supply chain locations
- **UX-7.3**: Geographic tag on activity cards
- **UX-7.4**: Geographic breakdown chart in results
- **UX-7.5**: Tooltip showing region-specific factors

### Acceptance Criteria
- [ ] User can select geography for each activity
- [ ] Calculations use region-specific factors
- [ ] Electricity carbon intensity varies by region
- [ ] Water stress weighting applied correctly
- [ ] Map visualization shows supply chain
- [ ] Geographic breakdown in results
- [ ] Transportation calculated between regions

---

## 8. Flexible Unit Scaling (P1)

### Overview
Allow calculations across various units (per item, per kg, per order, per year) for different use cases.

### User Stories
**As a** sustainability analyst
**I want to** calculate impacts per functional unit
**So that** results are meaningful for different contexts (e.g., per T-shirt vs. per kg textile)

### Functional Requirements

#### 8.1 Functional Unit Definition
- **FR-8.1.1**: Define functional unit for project
- **FR-8.1.2**: Common units:
  - Per item (e.g., per T-shirt)
  - Per kg (e.g., per kg textile)
  - Per m² (e.g., per square meter fabric)
  - Per use (e.g., per wear/wash cycle)
  - Per order (e.g., per customer order)
  - Per year (e.g., annual production)
  - Custom unit (user-defined)
- **FR-8.1.3**: Convert between units
- **FR-8.1.4**: Display results in selected unit

#### 8.2 Unit Conversion
- **FR-8.2.1**: Define conversion factors
- **FR-8.2.2**: Auto-convert when unit changes
- **FR-8.2.3**: Show results in multiple units simultaneously
- **FR-8.2.4**: Validate conversion logic

#### 8.3 Scaling Calculations
- **FR-8.3.1**: Scale up/down based on production volume
- **FR-8.3.2**: Calculate for batch (e.g., 100 T-shirts)
- **FR-8.3.3**: Scenario analysis with different volumes
- **FR-8.3.4**: Compare per-unit impacts across products

#### 8.4 Reference Flows
- **FR-8.4.1**: Define reference flow for each activity
- **FR-8.4.2**: Link reference flows to functional unit
- **FR-8.4.3**: Automatic scaling of flows
- **FR-8.4.4**: Display flow diagram

### Technical Requirements
- **TR-8.1**: Functional unit field in project schema
- **TR-8.2**: Unit conversion table in database
- **TR-8.3**: Calculation engine supports unit scaling
- **TR-8.4**: API endpoint: `GET /api/units`
- **TR-8.5**: Validation of unit compatibility

### UI/UX Requirements
- **UX-8.1**: Functional unit selector in project settings
- **UX-8.2**: Unit displayed consistently throughout app
- **UX-8.3**: Unit conversion calculator (utility)
- **UX-8.4**: Toggle between units in results view
- **UX-8.5**: Clear labeling of all quantities with units

### Acceptance Criteria
- [ ] User can define functional unit for project
- [ ] Results display in selected functional unit
- [ ] Conversion between units works correctly
- [ ] Can compare products with different functional units
- [ ] Batch scaling calculates correctly
- [ ] All quantities clearly labeled with units
- [ ] Unit conversion factors validated

---

## 9. Additional Features

### 9.1 Chat Support Integration (P2)
- **FR-9.1.1**: Integrate live chat support (Intercom or similar)
- **FR-9.1.2**: In-app help widget
- **FR-9.1.3**: Knowledge base / FAQ
- **FR-9.1.4**: Bug reporting tool
- **FR-9.1.5**: Feature request submission

### 9.2 User Onboarding (P1)
- **FR-9.2.1**: Interactive tutorial for new users
- **FR-9.2.2**: Sample project with pre-filled data
- **FR-9.2.3**: Video tutorials library
- **FR-9.2.4**: Contextual help tooltips
- **FR-9.2.5**: Quick start guide

### 9.3 Advanced Search & Filters (P2)
- **FR-9.3.1**: Global search across all projects
- **FR-9.3.2**: Filter by release, status, date, creator
- **FR-9.3.3**: Saved searches
- **FR-9.3.4**: Tag system for organization
- **FR-9.3.5**: Folder/collection organization

### 9.4 API & Integrations (P2)
- **FR-9.4.1**: Public API for external integrations
- **FR-9.4.2**: Zapier integration
- **FR-9.4.3**: Excel/Google Sheets add-in
- **FR-9.4.4**: PLM system integration
- **FR-9.4.5**: ERP system integration
- **FR-9.4.6**: Webhook support

### 9.5 Batch Processing (P1)
- **FR-9.5.1**: Batch import projects from CSV/Excel
- **FR-9.5.2**: Batch calculate multiple projects
- **FR-9.5.3**: Batch export reports
- **FR-9.5.4**: Bulk edit multiple projects
- **FR-9.5.5**: Progress tracking for batch operations

---

## Technical Architecture

### System Components

#### Frontend (React)
- **Component Library**: Material-UI or Ant Design
- **State Management**: Redux or Zustand
- **Charts**: Chart.js or Recharts
- **Maps**: Leaflet or Mapbox
- **Forms**: Formik + Yup validation
- **PDF Viewer**: react-pdf
- **Rich Text**: Draft.js or TipTap (for comments)

#### Backend (FastAPI)
- **Additional Libraries**:
  - `openpyxl`: Excel generation
  - `reportlab`: PDF generation
  - `celery`: Background job processing
  - `redis`: Caching and task queue
  - `python-docx`: Word document generation
  - `pandas`: Data manipulation for exports
  - `numpy`: Scientific calculations
  - `scikit-learn`: Future ML features

#### Database (MongoDB)
- **New Collections**:
  - `releases`: Version snapshots
  - `data_sources`: Source metadata
  - `comments`: Review comments
  - `review_assignments`: Review workflow
  - `impact_methods`: LCIA methods and factors
  - `geographic_data`: Regional factors
  - `export_jobs`: Background export tasks

#### Infrastructure
- **Job Queue**: Redis + Celery for background tasks
- **File Storage**: S3 or similar for generated reports
- **Email Service**: SendGrid or AWS SES
- **Real-time**: WebSocket (Socket.io or similar)
- **Caching**: Redis for calculation results

### Data Models

#### Release Schema
```json
{
  "_id": "ObjectId",
  "project_id": "ObjectId",
  "version": "1.0.0",
  "name": "Q1 2026 Release",
  "description": "Initial assessment release",
  "creator_id": "ObjectId",
  "created_at": "DateTime",
  "status": "locked",
  "tags": ["draft", "internal"],
  "snapshot": {
    "project_data": {},
    "activities": [],
    "calculations": {}
  },
  "change_log": ["Added 5 new activities", "Updated emission factors"],
  "notes": "Markdown text"
}
```

#### Data Source Schema
```json
{
  "_id": "ObjectId",
  "name": "Ecoinvent 3.8",
  "type": "database",
  "version": "3.8",
  "publisher": "Ecoinvent Association",
  "year": 2021,
  "geographic_scope": "Global",
  "technology_scope": "Current technology",
  "temporal_scope": "2015-2020",
  "quality_rating": 5,
  "url": "https://ecoinvent.org",
  "doi": "10.1000/example",
  "notes": "Standard LCA database",
  "created_by": "ObjectId",
  "created_at": "DateTime"
}
```

#### Comment Schema
```json
{
  "_id": "ObjectId",
  "project_id": "ObjectId",
  "activity_id": "ObjectId?",
  "user_id": "ObjectId",
  "parent_comment_id": "ObjectId?",
  "text": "Please verify this emission factor",
  "resolved": false,
  "created_at": "DateTime",
  "updated_at": "DateTime"
}
```

#### Review Assignment Schema
```json
{
  "_id": "ObjectId",
  "project_id": "ObjectId",
  "reviewer_id": "ObjectId",
  "assignee_id": "ObjectId",
  "status": "under_review",
  "deadline": "DateTime",
  "created_at": "DateTime",
  "completed_at": "DateTime?",
  "notes": "Focus on data quality"
}
```

### API Endpoints

#### Releases
- `POST /api/projects/{id}/releases` - Create release
- `GET /api/projects/{id}/releases` - List releases
- `GET /api/releases/{release_id}` - Get release details
- `PUT /api/releases/{release_id}` - Update release
- `DELETE /api/releases/{release_id}` - Delete release
- `GET /api/releases/{release_id}/compare/{other_id}` - Compare releases

#### Data Sources
- `POST /api/data-sources` - Create data source
- `GET /api/data-sources` - List data sources (filterable)
- `GET /api/data-sources/{id}` - Get source details
- `PUT /api/data-sources/{id}` - Update source
- `DELETE /api/data-sources/{id}` - Delete source

#### Export
- `POST /api/projects/{id}/export/pdf` - Generate PDF
- `POST /api/projects/{id}/export/excel` - Generate Excel
- `POST /api/projects/{id}/export/csv` - Generate CSV
- `GET /api/export-jobs/{job_id}` - Check export status
- `GET /api/export-jobs/{job_id}/download` - Download result

#### Review
- `POST /api/projects/{id}/submit-review` - Submit for review
- `POST /api/projects/{id}/assign-reviewer` - Assign reviewer
- `GET /api/reviews` - List reviews (for reviewer dashboard)
- `POST /api/reviews/{id}/approve` - Approve review
- `POST /api/reviews/{id}/request-changes` - Request changes

#### Comments
- `POST /api/comments` - Create comment
- `GET /api/projects/{id}/comments` - List comments
- `PUT /api/comments/{id}` - Update comment
- `DELETE /api/comments/{id}` - Delete comment
- `POST /api/comments/{id}/resolve` - Resolve comment

#### Visualization
- `GET /api/projects/{id}/visualizations/breakdown` - Impact breakdown data
- `GET /api/projects/{id}/visualizations/comparison` - Comparison data
- `GET /api/projects/{id}/visualizations/hotspots` - Hotspot analysis

---

## Implementation Roadmap

### Phase 1: Foundation (Weeks 1-4)
**Priority**: P0 features
**Goal**: Core functionality matching Earthster

#### Week 1-2: Release Management & Impact Categories
- [ ] Implement release data model and API
- [ ] Create releases UI (tab, list, create modal)
- [ ] Implement snapshot mechanism
- [ ] Add six impact categories to calculation engine
- [ ] Update results display for multiple categories

#### Week 3-4: Data Visualization
- [ ] Integrate charting library (Chart.js/Recharts)
- [ ] Implement pie chart for impact breakdown
- [ ] Implement bar charts for comparison
- [ ] Add interactive tooltips
- [ ] Implement chart export (PNG/SVG)
- [ ] Create dashboard view with key metrics

**Deliverables**:
- ✅ Release management working
- ✅ All six impact categories calculated
- ✅ Visual charts displaying results
- ✅ Basic export functionality

---

### Phase 2: Professional Features (Weeks 5-8)
**Priority**: P0-P1 features
**Goal**: Professional reporting and data transparency

#### Week 5-6: Export & Reporting
- [ ] Implement PDF generation (ReportLab)
- [ ] Create report templates (simple, detailed, executive)
- [ ] Implement Excel export with multiple sheets
- [ ] Add logo upload and customization
- [ ] Implement background job processing
- [ ] Create export UI and wizard

#### Week 7-8: Data Sources & Geographic
- [ ] Implement data source schema and API
- [ ] Create data sources UI
- [ ] Link data sources to activities
- [ ] Auto-generate bibliography
- [ ] Add geographic selection to activities
- [ ] Implement regional factors database
- [ ] Update calculations for geography

**Deliverables**:
- ✅ Professional PDF reports
- ✅ Excel export with all data
- ✅ Data source tracking
- ✅ Geographic-specific calculations

---

### Phase 3: Collaboration & Advanced (Weeks 9-12)
**Priority**: P1-P2 features
**Goal**: Team collaboration and advanced features

#### Week 9-10: Review Workflow
- [ ] Implement review status system
- [ ] Create review assignment API
- [ ] Build reviewer dashboard
- [ ] Implement commenting system
- [ ] Add email notifications
- [ ] Create review UI components

#### Week 11-12: Unit Scaling & Polish
- [ ] Implement functional unit system
- [ ] Add unit conversion logic
- [ ] Create unit selector UI
- [ ] Implement batch processing
- [ ] Add user onboarding tutorial
- [ ] Polish UI/UX across all features
- [ ] Performance optimization

**Deliverables**:
- ✅ Review workflow functional
- ✅ Flexible unit scaling
- ✅ Batch operations
- ✅ Onboarding experience

---

### Phase 4: Integrations & API (Weeks 13-16)
**Priority**: P2 features
**Goal**: External integrations and ecosystem

#### Week 13-14: Public API
- [ ] Design public API endpoints
- [ ] Implement authentication (API keys)
- [ ] Create API documentation (OpenAPI/Swagger)
- [ ] Rate limiting and usage tracking
- [ ] API console for testing

#### Week 15-16: Integrations
- [ ] Chat support integration (Intercom)
- [ ] Zapier integration
- [ ] Excel add-in (if applicable)
- [ ] Webhook system
- [ ] Final testing and bug fixes
- [ ] Launch preparation

**Deliverables**:
- ✅ Public API live
- ✅ Key integrations working
- ✅ Complete documentation
- ✅ Production-ready platform

---

## Success Metrics

### User Engagement
- **Target**: 500+ active users in first 6 months
- **Metric**: Weekly active users (WAU)
- **Goal**: 80% user retention month-over-month

### Feature Adoption
- **Release Management**: 70% of projects use releases
- **Data Visualization**: 90% of users view charts
- **PDF Export**: 60% of projects export reports
- **Review Workflow**: 40% of teams use review features
- **Impact Categories**: 80% of assessments use multiple categories

### Performance
- **Calculation Speed**: < 2 seconds for typical project
- **Report Generation**: < 30 seconds for PDF
- **Page Load Time**: < 1.5 seconds
- **API Response Time**: < 200ms (95th percentile)

### Quality
- **Bug Rate**: < 5 critical bugs per month
- **User Satisfaction**: > 4.5/5 stars
- **Support Tickets**: < 10% of users need support
- **Data Accuracy**: 99.9% calculation correctness

### Business
- **Conversion Rate**: 15% free to paid
- **Customer Acquisition Cost**: < $50
- **Lifetime Value**: > $500
- **Churn Rate**: < 5% monthly

---

## Risks & Mitigation

### Technical Risks

#### Risk 1: Calculation Complexity
**Risk**: Multi-category calculations are computationally intensive
**Impact**: High - affects core functionality
**Probability**: Medium
**Mitigation**:
- Implement caching for calculation results
- Use background jobs for intensive calculations
- Optimize algorithms and database queries
- Consider caching pre-calculated factors

#### Risk 2: Data Quality
**Risk**: Emission factors and regional data may be incomplete/inaccurate
**Impact**: High - affects result credibility
**Probability**: Medium
**Mitigation**:
- Source data from reputable databases (Ecoinvent, IPCC)
- Implement data quality indicators
- Allow users to override with custom data
- Regular data updates and validation

#### Risk 3: Scalability
**Risk**: Background job processing may bottleneck with many users
**Impact**: Medium - affects performance
**Probability**: Medium
**Mitigation**:
- Horizontal scaling with multiple workers
- Job queue monitoring and alerts
- Rate limiting on resource-intensive operations
- Performance testing before launch

### Product Risks

#### Risk 4: Feature Complexity
**Risk**: Too many features may overwhelm users
**Impact**: Medium - affects adoption
**Probability**: High
**Mitigation**:
- Phased rollout with progressive disclosure
- Comprehensive onboarding and tutorials
- Simple default settings with advanced options
- User testing and feedback loops

#### Risk 5: Competitive Landscape
**Risk**: Established players (Earthster, SimaPro) have network effects
**Impact**: Medium - affects growth
**Probability**: High
**Mitigation**:
- Focus on niche (fashion/textiles) initially
- Better UX and lower price point
- API-first approach for integrations
- Strong customer support and community

### Business Risks

#### Risk 6: Adoption Rate
**Risk**: Users may be reluctant to switch from existing tools
**Impact**: High - affects revenue
**Probability**: Medium
**Mitigation**:
- Free tier with generous limits
- Import from competitor formats
- Superior onboarding experience
- Case studies and success stories

---

## Open Questions

### Technical
1. Which LCIA method should be default? (ReCiPe 2016 recommended)
2. Should we support custom impact categories?
3. What's the maximum project size (activities/data)?
4. Cloud storage provider for reports? (AWS S3 vs. alternatives)
5. Real-time collaboration: necessary or nice-to-have?

### Product
1. Pricing model: per user, per project, or per assessment?
2. Free tier limits: how many projects/assessments?
3. Should releases be unlimited or capped per plan?
4. Required vs. optional impact categories?
5. Default to all six categories or let users select?

### Business
1. Target market: fashion brands only or broader?
2. B2B vs. B2C approach?
3. Partnership opportunities with data providers?
4. Certification/accreditation strategy?
5. Open-source components or fully proprietary?

---

## Appendix

### A. Glossary

**LCA**: Life Cycle Assessment - systematic analysis of environmental impacts

**LCIA**: Life Cycle Impact Assessment - phase of LCA translating inventory to impacts

**Functional Unit**: Quantified performance of a product system (e.g., "one T-shirt worn 50 times")

**Release**: Version snapshot of LCA project at a point in time

**Impact Category**: Type of environmental impact (e.g., climate change, water use)

**Characterization Factor**: Multiplier converting emissions to impact category units

**System Boundary**: What's included/excluded in the assessment

**DALY**: Disability-Adjusted Life Year - metric for human health impact

**PDF**: Potentially Disappeared Fraction - metric for ecosystem damage

**GWP**: Global Warming Potential - climate impact metric

### B. References

1. Earthster LCA Platform - https://app.earthster.org
2. ISO 14040:2006 - Environmental management — Life cycle assessment — Principles and framework
3. ISO 14044:2006 - Environmental management — Life cycle assessment — Requirements and guidelines
4. ReCiPe 2016 LCIA Method - https://www.rivm.nl/en/life-cycle-assessment-lca/recipe
5. Ecoinvent Database - https://ecoinvent.org
6. IPCC GHG Emission Factors - https://www.ipcc.ch

### C. Competitive Analysis

| Feature | EUFSI (Current) | EUFSI (Proposed) | Earthster | SimaPro | GaBi |
|---------|-----------------|------------------|-----------|---------|------|
| Release Management | ❌ | ✅ | ✅ | ✅ | ✅ |
| Impact Categories | 1 (carbon) | 6+ | 6+ | 18+ | 16+ |
| Data Visualization | Basic | Advanced | Good | Advanced | Advanced |
| PDF Reports | Basic | Professional | Yes | Yes | Yes |
| Review Workflow | ❌ | ✅ | ✅ | ⚠️ | ⚠️ |
| Geographic | ❌ | ✅ | ✅ | ✅ | ✅ |
| API | ❌ | ✅ | ⚠️ | ⚠️ | ❌ |
| Price | Free | Freemium | $$ | $$$ | $$$ |
| Ease of Use | Good | Excellent | Good | Medium | Medium |

### D. User Research Summary

**Need**: 15 potential users interviewed (sustainability analysts, brand managers)

**Key Findings**:
1. 80% want visual impact breakdowns (pie/bar charts)
2. 70% need professional PDF reports for stakeholders
3. 60% require multi-category assessment (not just carbon)
4. 50% need version control/audit trail
5. 40% want collaborative review workflows
6. 30% want API for integration with PLM systems

**Pain Points with Current Tools**:
1. Too complex (SimaPro, GaBi)
2. Too expensive for small teams
3. Lack of modern UI/UX
4. Poor export/reporting options
5. No collaboration features

**Desired Features** (ranked by frequency):
1. Better visualization (13/15 users)
2. Easier data entry (12/15 users)
3. PDF export (11/15 users)
4. Multi-category assessment (10/15 users)
5. Version control (9/15 users)
6. Team collaboration (7/15 users)

---

## Approval & Sign-off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Product Owner | [Name] | [Date] | _________ |
| Engineering Lead | [Name] | [Date] | _________ |
| Design Lead | [Name] | [Date] | _________ |
| Stakeholder | [Name] | [Date] | _________ |

---

**Document Version**: 1.0
**Last Updated**: 2026-01-08
**Next Review**: 2026-02-08
**Contact**: [Product Owner Email]

---

## Next Steps

1. **Review this PRD** with stakeholders
2. **Prioritize features** based on business goals
3. **Create detailed technical specs** for Phase 1
4. **Set up project in Jira/Linear** with epics and stories
5. **Assign engineering resources**
6. **Begin Sprint 1** - Release Management implementation
7. **Schedule weekly check-ins** for progress review

**Ready to start implementation? Let's build an amazing LCA tool!** 🚀
