# ECU Map Lab - Future Development Plans

## Current Status Summary

### ✅ Completed (Phase 1 - Backend Foundation)
- Mock data generator for stock and tuned maps
- CSV map parsing with deduplication and NaN handling
- FastAPI REST API with `/api/maps/parse` endpoint
- Grid interpolation using scipy
- Comprehensive pytest test suite
- Project structure and documentation

---

## Missing Core Features (From Original Requirements)

### 🔴 High Priority - Core Functionality

#### 1. Frontend Application
**Status:** Not Started  
**Priority:** Critical

- React application structure
- File upload component for CSV maps
- Interactive 3D map visualization using Plotly.js
- 2D cross-section views
- Map overlay/comparison (stock vs tuned)
- Difference map visualization
- Cell editing capabilities
- Export edited maps to CSV
- Toggle between different views (3D surface, difference, slices)

**Implementation Notes:**
- Set up React with Vite or Create React App
- Integrate Plotly.js for 3D surface plots
- Create components: MapUploader, Map3DViewer, MapComparator, MapEditor
- API integration with FastAPI backend
- State management (React Context or Redux)

#### 2. Map Difference Computation
**Status:** Not Started  
**Priority:** High

- Endpoint: `/api/maps/diff` to compute differences between two maps
- Statistical analysis (min, max, mean, std deviation of differences)
- Return difference grid in JSON format
- Handle maps with different axis ranges (interpolation/extrapolation)
- Visualize differences in frontend

**Backend Implementation:**
- Service function: `compute_map_difference(map1, map2)`
- Handle dimension mismatches
- Calculate statistics
- Return difference grid with metadata

#### 3. Map Smoothing and Masking
**Status:** Not Started  
**Priority:** Medium

- Endpoint: `/api/maps/smooth` for applying smoothing algorithms
- Endpoint: `/api/maps/mask` for applying masks (e.g., safe zones)
- Support multiple smoothing methods (Gaussian, moving average)
- Apply masks based on constraints (RPM limits, load limits, safety thresholds)

**Implementation:**
- Service functions for smoothing algorithms
- Mask definition structure (JSON config)
- Validation and application logic

#### 4. Constrained Optimizer
**Status:** Not Started  
**Priority:** High

- Endpoint: `/api/maps/optimize` for suggesting timing adjustments
- Genetic algorithm implementation (using DEAP library)
- Constraint definition system:
  - Maximum timing advance limits
  - Safe operating zones
  - Performance targets (torque, power surrogates)
- Return optimized timing grid with safety validation

**Implementation:**
- Optimization service module
- Constraint definition models
- GA setup with DEAP
- Objective function (performance surrogate)
- Constraint validation

#### 5. Map Management Endpoints
**Status:** Not Started  
**Priority:** Medium

- `GET /api/maps/` - List all uploaded maps
- `GET /api/maps/{id}` - Get specific map by ID
- `DELETE /api/maps/{id}` - Delete a map
- `POST /api/maps/` - Save/upload a new map
- Database or file storage for map persistence

**Implementation:**
- Map metadata model (ID, name, type, date, description)
- Storage solution (SQLite, file system, or PostgreSQL for production)
- CRUD operations
- Map validation before saving

---

## Additional Backend Features

### 6. Advanced Map Operations
- **Interpolation methods:** Linear, cubic, spline options
- **Extrapolation:** Handle edge cases at boundaries
- **Map validation:** Check for unrealistic values, out-of-range data
- **Map normalization:** Scale maps to standard axes
- **Map merging:** Combine multiple maps with priority rules

### 7. Performance Metrics
- **Torque estimation:** Calculate estimated torque from timing map
- **Power calculation:** Surrogate models for power estimation
- **Efficiency metrics:** Fuel economy impact calculations
- **Safety scoring:** Rate map safety based on constraints

### 8. API Enhancements
- **Authentication:** User accounts and API keys (if needed)
- **Rate limiting:** Protect endpoints from abuse
- **Caching:** Cache parsed maps for performance
- **Pagination:** For map lists
- **Filtering/Search:** Find maps by criteria
- **Bulk operations:** Parse/process multiple maps at once

### 9. Data Export Formats
- **JSON export:** Full map data with metadata
- **Image export:** PNG/JPG of 3D visualization
- **Multiple CSV formats:** Different pivot styles
- **Binary formats:** For ECU compatibility (if applicable)

---

## Frontend Features

### 10. Advanced Visualization
- **Multiple map comparison:** Side-by-side or overlay
- **Animated transitions:** When switching between maps
- **Crosshair/cursor tracking:** Show values at cursor position
- **Zoom and pan:** Interactive map navigation
- **Customizable color schemes:** For better visualization
- **2D heatmaps:** Alternative to 3D surface
- **Contour plots:** For detailed analysis

### 11. Map Editor
- **Cell-by-cell editing:** Click and edit individual cells
- **Bulk operations:** Select regions and apply changes
- **Undo/Redo:** Edit history
- **Validation feedback:** Highlight unsafe/invalid values
- **Copy/paste:** Between maps or regions
- **Formulas:** Apply formulas to regions (e.g., +2 degrees across load range)

### 12. User Interface
- **Dashboard:** Overview of all maps
- **Project management:** Organize maps into projects/tunes
- **Settings:** Customize visualization preferences
- **Help/Documentation:** In-app guides
- **Keyboard shortcuts:** For power users
- **Dark mode:** UI theme option

---

## Testing & Quality

### 13. Test Coverage Expansion
- **API endpoint tests:** Test all endpoints with various inputs
- **Integration tests:** Full workflow tests
- **Frontend tests:** React component testing (Jest, React Testing Library)
- **E2E tests:** Full user workflow (Playwright, Cypress)
- **Performance tests:** Load testing for API

### 14. Code Quality
- **Type hints:** Complete Python type hints
- **Linting:** ESLint for frontend, pylint/ruff for backend
- **Code formatting:** Prettier, Black
- **Pre-commit hooks:** Automated checks before commits

---

## Documentation

### 15. Documentation Enhancement
- **API documentation:** Complete endpoint documentation (OpenAPI/Swagger)
- **User guide:** How to use the application
- **Developer guide:** How to extend/contribute
- **Jupyter notebooks:** Tutorial notebooks for learning map transformations
  - CSV → Pivot → Meshgrid → Plot examples
  - Interpolation techniques
  - Optimization walkthrough
- **Video tutorials:** Screen recordings for key features

---

## Infrastructure & DevOps

### 16. Deployment
- **Docker:** Dockerfile for backend and frontend
- **Docker Compose:** Full stack deployment
- **GitHub Actions CI:** Automated testing on PRs
- **CI/CD pipeline:** Automated deployment
- **Environment config:** .env files for configuration

### 17. Production Readiness
- **Error logging:** Proper logging with rotation
- **Monitoring:** Health checks, metrics
- **Database:** Proper data persistence (PostgreSQL recommended)
- **Security:** Input validation, SQL injection prevention, CORS
- **Performance:** Caching, query optimization
- **Backup:** Data backup strategies

---

## Advanced Features (Future Phases)

### 18. Machine Learning Integration
- **Map prediction:** Suggest tuning based on similar maps
- **Anomaly detection:** Identify unsafe or unusual map values
- **Optimization AI:** ML-based optimizer alternative to GA

### 19. Real-Time Simulation
- **Engine simulator:** Simulate engine response to map changes
- **Performance prediction:** Estimate power/torque curves from maps
- **Virtual dyno:** Simulate dyno runs

### 20. Collaboration Features
- **Map sharing:** Share maps with other users
- **Version control:** Track map changes over time
- **Comments/Annotations:** Add notes to specific map regions
- **Community library:** Repository of shared maps

### 21. ECU Integration (Hardware)
- **ECU file format support:** Read/write ECU-specific formats
- **Live data connection:** Connect to ECU for real-time monitoring
- **Flash tools:** Tools to write maps to ECU (advanced, hardware-dependent)

---

## Recommended Development Order

### Phase 2: Frontend Foundation (Next Sprint)
1. Set up React application structure
2. Create basic file upload component
3. Integrate Plotly.js for 3D visualization
4. Connect to FastAPI backend
5. Display parsed map in 3D view

### Phase 3: Core Visualization Features
1. Map comparison (overlay two maps)
2. Difference map computation (backend + frontend)
3. 2D cross-section views
4. Basic cell editing

### Phase 4: Advanced Features
1. Constrained optimizer (backend)
2. Map smoothing and masking
3. Map management (CRUD operations)
4. Export functionality

### Phase 5: Polish & Production
1. UI/UX improvements
2. Comprehensive testing
3. Documentation completion
4. Docker deployment
5. CI/CD setup

---

## Technical Debt & Improvements

### Current Limitations
- No persistent storage (maps only exist during request)
- No error recovery for large files
- Limited interpolation options (only linear)
- No map validation beyond basic parsing
- No authentication/authorization
- No rate limiting

### Code Improvements
- Add async/await throughout backend for better performance
- Implement proper error handling middleware
- Add request validation using Pydantic models
- Implement caching layer
- Add logging infrastructure
- Refactor map_parser for better modularity

---

## Notes

- All frontend features depend on completing the React application setup first
- Backend features can be developed independently
- Prioritize features that provide immediate learning value
- Consider user feedback after Phase 2 to guide further development
- Keep educational focus - features should help users understand tuning concepts

---

**Last Updated:** 2025-01-11  
**Current Phase:** Phase 1 Complete ✅  
**Next Phase:** Phase 2 - Frontend Foundation

