# EUFSI LCA Tool - Product Requirements Document

## Overview
A Real Brightway2-Powered Multi-Industry Life Cycle Assessment (LCA) Tool supporting comprehensive environmental impact analysis across Textile, Footwear, Construction, and Battery industries.

## User Personas
1. **LCA Practitioners** - Environmental consultants performing detailed product assessments
2. **Sustainability Professionals** - Corporate sustainability teams tracking product footprints
3. **Product Designers** - Engineers optimizing product environmental performance
4. **Compliance Officers** - Ensuring regulatory environmental compliance

## Core Requirements (Static)
- Real Brightway2 LCA calculation engine (no simulated data)
- Support for USLCI, Agribalyse, FORWAST databases
- Full ReCiPe and EF 3.1 methodology (16+ impact categories)
- Multi-industry support: Textile, Footwear, Construction, Battery
- Scope selection: Cradle-to-Gate, Cradle-to-Grave, Both (comparison)
- PDF report generation
- EU Commission blue/white branding

## What's Been Implemented ✓
**Date: January 5, 2025**

### Backend (FastAPI)
- ✓ Real Brightway2 integration with activity mapping
- ✓ USLCI, Agribalyse, FORWAST database support
- ✓ Full ReCiPe (18 categories) and EF 3.1 (16 categories) methods
- ✓ Industry-specific input schemas (Textile, Footwear, Construction, Battery)
- ✓ Project CRUD operations with MongoDB storage
- ✓ Asynchronous LCA calculation with status tracking
- ✓ Contribution analysis by life cycle stage
- ✓ PDF report generation with ReportLab
- ✓ Emission factor-based impact estimation
- ✓ **NEW: Impact Traceability API** - Trace origin of impacts with activities, exchanges, characterization factors

### Frontend (React)
- ✓ Homepage with EU branding and industry selection cards
- ✓ Multi-step assessment wizard with dynamic form generation
- ✓ Configuration page (database, method, scope selection)
- ✓ Results dashboard with multiple visualizations:
  - Summary cards (Climate Change, Water Use, Fossil Depletion)
  - Bar chart (Top 10 Impact Categories)
  - Radar chart (Environmental Profile)
  - Pie chart (Contribution by Life Cycle Stage)
  - Tabbed interface (Overview, Impact Categories, Contributions, **Impact Trace**)
- ✓ PDF download functionality
- ✓ Project history with search and filter
- ✓ Responsive design with EU Commission styling
- ✓ **NEW: Impact Traceability Component** - Interactive trace with expandable activities and exchange details

### Input Schema (Textile - from Excel)
- Product Information
- Fiber Composition (15+ materials)
- Yarn Production (11 spinning methods)
- Fabric Production (10+ construction methods)
- Dyeing/Finishing (16+ processes)
- Manufacturing
- Production Locations & Energy
- Transportation (5 modes)
- Use Phase
- End of Life

## Prioritized Backlog

### P0 - Critical (Not Started)
- None remaining

### P1 - High Priority
1. Direct URL routing for assessment wizard (`/assessment/textile`)
2. Edit existing project functionality
3. Input validation with error messages

### P2 - Medium Priority
1. Benchmarking & hotspot analysis
2. Improvement suggestions
3. Project comparison feature
4. CSV export option

### P3 - Low Priority
1. User authentication
2. Team collaboration features
3. API rate limiting
4. Advanced filtering in history

## Technical Architecture
```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│     React       │────▶│    FastAPI      │────▶│    MongoDB      │
│   Frontend      │     │    Backend      │     │   Database      │
│   (Port 3000)   │     │   (Port 8001)   │     │                 │
└─────────────────┘     └────────┬────────┘     └─────────────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │   Brightway2    │
                        │   LCA Engine    │
                        │   (USLCI/etc)   │
                        └─────────────────┘
```

## API Endpoints
- `GET /api/` - Health check
- `GET /api/industries` - List available industries
- `GET /api/industries/{industry}/schema` - Get input schema
- `GET /api/lca/databases` - List LCA databases
- `GET /api/lca/methods` - List LCIA methods
- `GET /api/lca/impact-categories/{method}` - Get impact categories for method
- `GET /api/lca/stages/{industry}` - Get life cycle stages for industry
- `GET /api/lca/trace/{project_id}` - **NEW** Trace impact origin (with query params: impact_category, life_cycle_stage)
- `POST /api/projects` - Create project
- `GET /api/projects` - List all projects
- `GET /api/projects/{id}` - Get project details
- `PUT /api/projects/{id}/input-data` - Update input data
- `DELETE /api/projects/{id}` - Delete project
- `POST /api/lca/calculate/{id}` - Start calculation
- `GET /api/lca/results/{id}` - Get results
- `GET /api/reports/{id}/pdf` - Generate PDF

## Next Steps
1. Add direct URL routing for assessment wizard
2. Implement project editing capability
3. Add input validation feedback
4. Consider benchmarking feature for future release
