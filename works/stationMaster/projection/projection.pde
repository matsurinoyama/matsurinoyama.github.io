import java.util.*;

// Optional: limit cache growth and scale images to reduce memory usage over long runs
// Lowered defaults to reduce memory pressure that can cause "Target VM failed to initialize" on startup.
final int MAX_CACHE_IMAGES = 120;      // cap the number of textures kept in memory (lower = safer)
final int MAX_TEX_WIDTH = 1600;        // scale down wide images (0 = no limit)
final int MAX_TEX_HEIGHT = 900;        // scale down tall images (0 = no limit)
final boolean SHOW_MEM_STATS = true;   // overlay memory / loader info
final boolean USE_FULLSCREEN = false;  // fallback to window size if fullscreen causes VM init failure
final int WINDOW_W = 1920;
final int WINDOW_H = 1080;

PImage img;
int cols = 7;
int rows = 7;

PVector[][] points;
int draggedI = -1, draggedJ = -1;
float dragThreshold = 10;
boolean editMode = false;
boolean dragAllMode = false;
PVector dragAllOffset = new PVector(0, 0);

// Hot-reload settings
// Watch the top-level `faces` folder under works/stationMaster
String WATCH_DIR = "../faces"; // relative to sketch folder
int POLL_INTERVAL_MS = 1500; // how often to scan folder for changes

ArrayList<String> imageFiles; // absolute paths
int currentImageIndex = 0;
int lastImageChange = 0;
int imageChangeInterval = 7500; // 7.5 seconds

// Track newest file for change detection
String lastNewestName = null;
HashSet<String> lastFileSet = null; // track actual file list to detect changes
boolean newFileTransitioning = false; // flag to prevent normal cycling during new file transition

HashMap<String, PImage> textureCache = new HashMap<String, PImage>();
// Track usage order for a simple LRU eviction policy
ArrayDeque<String> cacheOrder = new ArrayDeque<String>(); // most-recently used at tail
HashMap<String, Long> mtimes = new HashMap<String, Long>();
ArrayList<String> loadQueue = new ArrayList<String>(); // absolute paths
long lastPoll = 0;

// Crossfade / transition state
boolean transitioning = false;
int transitionDuration = 1500; // ms, smooth crossfade (shorter than imageChangeInterval)
long transitionStart = 0;
PImage imgPrev = null;
PImage imgNext = null;
PGraphics pgPrev = null;
PGraphics pgNext = null;

void setup() {
  fullScreen(P3D);
  
  // Ensure the watch folder exists
  File wd = new File(sketchPath(WATCH_DIR));
  if (!wd.exists()) wd.mkdirs();

  // Initial scan + queue loads
  pollFolderAndQueueLoads();

  // Start background loader thread
  Thread loader = new Thread(new Runnable() {
    public void run() {
      while (true) {
        String nextFile = null;
        synchronized (loadQueue) {
          if (!loadQueue.isEmpty()) nextFile = loadQueue.remove(0);
        }
        if (nextFile != null) {
          try {
            PImage loaded = null;
            try {
              loaded = loadImage(nextFile);
            } catch (OutOfMemoryError oom) {
              println("[loader][OOM] OutOfMemory while loading. Evicting half of cache & requesting GC.");
              emergencyCacheTrim();
              System.gc();
              continue; // skip this cycle
            }
            if (loaded != null) {
              // Optionally scale large textures down to reduce memory usage
              if ((MAX_TEX_WIDTH > 0 && loaded.width > MAX_TEX_WIDTH) || (MAX_TEX_HEIGHT > 0 && loaded.height > MAX_TEX_HEIGHT)) {
                float sx = MAX_TEX_WIDTH > 0 ? (float)MAX_TEX_WIDTH / loaded.width : 1.0f;
                float sy = MAX_TEX_HEIGHT > 0 ? (float)MAX_TEX_HEIGHT / loaded.height : 1.0f;
                float s = min(sx, sy);
                if (s < 1.0f) {
                  int nw = max(1, round(loaded.width * s));
                  int nh = max(1, round(loaded.height * s));
                  loaded.resize(nw, nh);
                }
              }
              String name = new File(nextFile).getName();
              putTexture(name, loaded);
              println("[loader] loaded -> " + name + " (bytes=" + (loaded.width * loaded.height) + ")");
              
              // Check if this is a newly uploaded file that needs immediate transition
              if (imageFiles != null && imageFiles.size() > 0) {
                String newestName = new File(imageFiles.get(0)).getName();
                if (name.equals(newestName) && currentImageIndex == 0 && img != null && !transitioning) {
                  // This is the newest file and we're waiting for it - start transition now!
                  println("[loader] Triggering transition to newly loaded: " + name);
                  imgPrev = img;
                  imgNext = loaded;
                  transitionStart = millis();
                  transitioning = true;
                  newFileTransitioning = true;
                  // Reset timer so the new image shows for full duration after transition completes
                  lastImageChange = millis();
                }
              }
              
              // If this is the currently selected image, update img reference
              String currentName = getCurrentImageName();
              if (currentName != null && currentName.equals(name)) {
                PImage cur = getTexture(name);
                if (cur != null) img = cur;
              }
            }
          } catch (Exception e) {
            println("Loader thread error: " + e.getMessage());
          }
        } else {
          try { Thread.sleep(150); } catch (InterruptedException e) {}
        }
      }
    }
  });
  loader.setDaemon(true);
  loader.start();

  // Do not exit if no images yet; wait for dynamic additions
  resetPoints();
  loadCoordinates();
  lastImageChange = millis();
}

void loadImageFiles() {
  imageFiles = new ArrayList<String>();
  File dir = new File(sketchPath(WATCH_DIR));
  if (dir.exists() && dir.isDirectory()) {
    File[] files = dir.listFiles();
    if (files == null) return;
    for (File file : files) {
      String name = file.getName();
      String nameLower = name.toLowerCase();
      if (nameLower.startsWith("aligned_") && (nameLower.endsWith(".jpg") || nameLower.endsWith(".png") || nameLower.endsWith(".jpeg"))) {
        imageFiles.add(file.getAbsolutePath());
      }
    }
    // Sort by sequential number (highest -> lowest) so newest uploads appear first
    Collections.sort(imageFiles, new Comparator<String>() {
      public int compare(String a, String b) {
        int numA = extractNumber(new File(a).getName());
        int numB = extractNumber(new File(b).getName());
        // Descending order: highest number first
        return Integer.compare(numB, numA);
      }
    });
  }
  if (imageFiles.size() > 0) {
    println("Found " + imageFiles.size() + " images in " + WATCH_DIR);
    // Debug: print sorted order
    println("Sorted order (highest to lowest):");
    for (int i = 0; i < min(10, imageFiles.size()); i++) {
      String name = new File(imageFiles.get(i)).getName();
      int num = extractNumber(name);
      println("  [" + i + "] " + name + " (num=" + num + ")");
    }
  }
}

// Extract sequential number from aligned_N.ext filename (returns 0 if invalid)
int extractNumber(String filename) {
  try {
    // "aligned_123.jpg" -> "123"
    // Handle case-insensitive matching
    if (!filename.toLowerCase().startsWith("aligned_")) return 0;
    int dotIndex = filename.lastIndexOf('.');
    String numStr = (dotIndex > 0) ? filename.substring(8, dotIndex) : filename.substring(8);
    return Integer.parseInt(numStr);
  } catch (Exception e) {
    return 0;
  }
}

// Return the filename (not path) of the currently selected image, or null
String getCurrentImageName() {
  if (imageFiles == null || imageFiles.size() == 0) return null;
  if (currentImageIndex < 0 || currentImageIndex >= imageFiles.size()) return null;
  return new File(imageFiles.get(currentImageIndex)).getName();
}


void pollFolderAndQueueLoads() {
  // Scan directory for current files
  File dir = new File(sketchPath(WATCH_DIR));
  HashSet<String> currentNames = new HashSet<String>();
  if (dir.exists() && dir.isDirectory()) {
    File[] files = dir.listFiles();
    if (files != null) {
      for (File file : files) {
        String name = file.getName();
        String nameLower = name.toLowerCase();
        if (nameLower.startsWith("aligned_") && (nameLower.endsWith(".jpg") || nameLower.endsWith(".png") || nameLower.endsWith(".jpeg"))) {
          currentNames.add(name);
        }
      }
    }
  }
  
  // Only reload/resort if file set changed
  boolean fileSetChanged = (lastFileSet == null || !lastFileSet.equals(currentNames));
  if (fileSetChanged) {
    println("[poll] File set changed. Reloading and sorting...");
    loadImageFiles();
    lastFileSet = new HashSet<String>(currentNames);
    
    // Reset to newest image when files change
    if (imageFiles != null && imageFiles.size() > 0) {
      String newestName = new File(imageFiles.get(0)).getName();
      
      // Immediately transition to newest file
      PImage newestTex = getTexture(newestName);
      println("[new-file] newestTex=" + (newestTex != null ? "loaded" : "null") + ", img=" + (img != null ? "exists" : "null") + ", transitioning=" + transitioning);
      
      if (newestTex != null) {
        // If we have a current image showing, transition smoothly
        if (img != null) {
          // Cancel any ongoing transition first
          if (transitioning) {
            println("[new-file] Canceling ongoing transition");
            transitioning = false;
            if (imgNext != null) img = imgNext; // complete to the target
            imgPrev = null;
            imgNext = null;
            if (pgPrev != null) { pgPrev.dispose(); pgPrev = null; }
            if (pgNext != null) { pgNext.dispose(); pgNext = null; }
          }
          
          // Now start smooth transition to newest image
          println("[new-file] Setting up transition: imgPrev=" + img + ", imgNext=" + newestTex);
          imgPrev = img;
          imgNext = newestTex;
          transitionStart = millis();
          transitioning = true;
          newFileTransitioning = true;
          println("[new-file] Transition started! transitioning=" + transitioning + ", newFileTransitioning=" + newFileTransitioning);
          
          // Set timer so next cycle happens AFTER transition completes + full display time
          lastImageChange = millis() - (imageChangeInterval - transitionDuration);
        } else {
          // No current image, just set it directly
          img = newestTex;
          println("[new-file] Set first image to newest: " + newestName);
          lastImageChange = millis();
        }
        
        currentImageIndex = 0;
      } else {
        // Texture not loaded yet, reset to show it as soon as it loads
        currentImageIndex = 0;
        lastImageChange = millis();
        println("[new-file] Queued newest (not loaded yet): " + newestName);
      }
      
      lastNewestName = newestName;
    }
  }
  
  // Track file changes and queue loads
  if (imageFiles != null && imageFiles.size() > 0) {
    
    // Track file changes and queue loads
    for (String abs : imageFiles) {
      File f = new File(abs);
      String name = f.getName();
      long mtime = f.lastModified();
      Long known = mtimes.get(name);
      if (known == null || known.longValue() != mtime) {
        mtimes.put(name, mtime);
        synchronized (loadQueue) {
          if (!loadQueue.contains(abs)) loadQueue.add(abs);
        }
      }
    }
  }

  // Remove deleted files from mtimes and texture cache
  ArrayList<String> toRemove = new ArrayList<String>();
  for (String knownName : mtimes.keySet()) {
    if (!currentNames.contains(knownName)) toRemove.add(knownName);
  }
  for (String n : toRemove) {
    mtimes.remove(n);
    synchronized (textureCache) {
      textureCache.remove(n);
    }
  }

  // Ensure there's a currentImageIndex when images exist
  if ((imageFiles != null) && imageFiles.size() > 0) {
    if (currentImageIndex < 0 || currentImageIndex >= imageFiles.size()) currentImageIndex = 0;
    // if img is null or the current image is not loaded yet, queue it
    String curName = getCurrentImageName();
    if (curName != null) {
      synchronized (textureCache) {
        if (!textureCache.containsKey(curName)) {
          String abs = imageFiles.get(currentImageIndex);
          synchronized (loadQueue) {
            if (!loadQueue.contains(abs)) loadQueue.add(abs);
          }
        }
      }
    }
  }
}

void resetPoints() {
  points = new PVector[rows][cols];
  float w = width * 0.4;
  float h = height * 0.6;
  float startX = (width - w) / 2;
  float startY = (height - h) / 2;

  for (int j = 0; j < rows; j++) {
    for (int i = 0; i < cols; i++) {
      float x = map(i, 0, cols-1, startX, startX + w);
      float y = map(j, 0, rows-1, startY, startY + h);
      points[j][i] = new PVector(x, y, 0);
    }
  }
}

void draw() {
  // Poll folder periodically for changes
  if (millis() - lastPoll > POLL_INTERVAL_MS) {
    lastPoll = millis();
    pollFolderAndQueueLoads();
  }

  // Normal cycling behavior: advance every interval (but not during new-file transition)
  if (!newFileTransitioning && millis() - lastImageChange > imageChangeInterval && imageFiles != null && imageFiles.size() > 0) {
    int nextIndex = (currentImageIndex + 1) % imageFiles.size();
    String nextName = new File(imageFiles.get(nextIndex)).getName();
    int nextNum = extractNumber(nextName);
    println("[cycle] Moving from index " + currentImageIndex + " to " + nextIndex + " (" + nextName + ", num=" + nextNum + ")");
    PImage nextTex = getTexture(nextName);
    if (nextTex != null) {
      // start transition only when we actually have the texture
      beginTransition(nextTex);
      currentImageIndex = nextIndex;
      lastImageChange = millis(); // update timer only on success
    } else {
      // queue load (absolute path) and try again soon without resetting timer
      String abs = imageFiles.get(nextIndex);
      synchronized (loadQueue) { if (!loadQueue.contains(abs)) loadQueue.add(abs); }
      // do not update lastImageChange so we re-attempt promptly
    }
  }
  
  background(0);
  noStroke();
  noFill();
  textureMode(IMAGE);

  // If img is null, skip texture coordinates and draw black placeholder
  if (img == null) {
    fill(0);
    rect(0,0,width,height);
    fill(255);
    textAlign(CENTER, CENTER);
    textSize(24);
    text("Waiting for textures...", width/2, height/2);
    return;
  }

  // Draw the mesh (texture mapped) with crossfade support
  if (transitioning) {
    float t = constrain((millis() - transitionStart) / (float)transitionDuration, 0, 1);
    // smoothstep easing
    t = t * t * (3 - 2 * t);

  // render previous and next into PGraphics
    if (pgPrev == null) pgPrev = createGraphics(width, height, P3D);
    if (pgNext == null) pgNext = createGraphics(width, height, P3D);

    drawMeshTo(pgPrev, imgPrev);
    drawMeshTo(pgNext, imgNext);

    // draw blended result
    pushStyle();
    imageMode(CORNER);
    tint(255, 255 * (1 - t));
    image(pgPrev, 0, 0);
    tint(255, 255 * t);
    image(pgNext, 0, 0);
    noTint();
    popStyle();

    if (t >= 1) {
      // finish transition
      transitioning = false;
      newFileTransitioning = false;
      img = imgNext;
      imgPrev = null;
      imgNext = null;
      if (pgPrev != null) { pgPrev.dispose(); pgPrev = null; }
      if (pgNext != null) { pgNext.dispose(); pgNext = null; }
    }
  } else {
    // Normal single texture render
    drawMeshTo(null, img);
  }

  // Draw editable points
  if (editMode) {
    stroke(255, 50);
    for (int j = 0; j < rows; j++) {
      for (int i = 0; i < cols; i++) {
        if (i < cols - 1) line(points[j][i].x, points[j][i].y, points[j][i + 1].x, points[j][i + 1].y);
        if (j < rows - 1) line(points[j][i].x, points[j][i].y, points[j + 1][i].x, points[j + 1][i].y);
      }
    }
    noStroke();
    fill(255, 0, 0);
    for (int j = 0; j < rows; j++) {
      for (int i = 0; i < cols; i++) {
        ellipse(points[j][i].x, points[j][i].y, 10, 10);
      }
    }
  }

  if (SHOW_MEM_STATS) drawMemoryStats();
}

// Render the mesh with given texture into either the screen (if pg==null) or a PGraphics
void drawMeshTo(PGraphics pg, PImage tex) {
  PGraphics target = (pg == null) ? (PGraphics)g : pg;
  if (pg != null) {
    target.beginDraw();
    target.background(0);
    target.noStroke();
    target.textureMode(IMAGE);
  } else {
    target.noStroke();
    target.textureMode(IMAGE);
  }

  target.beginShape(QUADS);
  if (tex != null) target.texture(tex);
  for (int j = 0; j < rows - 1; j++) {
    for (int i = 0; i < cols - 1; i++) {
      float u1 = i / float(cols - 1);
      float v1 = j / float(rows - 1);
      float u2 = (i + 1) / float(cols - 1);
      float v2 = (j + 1) / float(rows - 1);

      PVector p1 = points[j][i];
      PVector p2 = points[j][i + 1];
      PVector p3 = points[j + 1][i + 1];
      PVector p4 = points[j + 1][i];

      target.vertex(p1.x, p1.y, p1.z, u1 * (tex != null ? tex.width : 1), v1 * (tex != null ? tex.height : 1));
      target.vertex(p2.x, p2.y, p2.z, u2 * (tex != null ? tex.width : 1), v1 * (tex != null ? tex.height : 1));
      target.vertex(p3.x, p3.y, p3.z, u2 * (tex != null ? tex.width : 1), v2 * (tex != null ? tex.height : 1));
      target.vertex(p4.x, p4.y, p4.z, u1 * (tex != null ? tex.width : 1), v2 * (tex != null ? tex.height : 1));
    }
  }
  target.endShape();

  if (pg != null) target.endDraw();
}

void beginTransition(PImage nextImg) {
  if (nextImg == null) return;
  if (transitioning) return; // ignore if already transitioning
  imgPrev = img;
  imgNext = nextImg;
  transitionStart = millis();
  transitioning = true;
  println("[transition] from " + (imgPrev==null?"<none>":"imgPrev") + " to " + (imgNext==null?"<none>":"imgNext") + " at " + transitionStart);
}

// --- Cache helpers (thread-safe) ---
void touchOrder(String name) {
  synchronized (cacheOrder) {
    // remove and re-add to mark as most-recently used
    cacheOrder.remove(name);
    cacheOrder.addLast(name);
  }
}

PImage getTexture(String name) {
  synchronized (textureCache) {
    PImage tex = textureCache.get(name);
    if (tex != null) touchOrder(name);
    return tex;
  }
}

void putTexture(String name, PImage tex) {
  synchronized (textureCache) {
    textureCache.put(name, tex);
  }
  touchOrder(name);
  enforceCacheLimit();
}

void enforceCacheLimit() {
  if (MAX_CACHE_IMAGES <= 0) return;
  synchronized (textureCache) {
    synchronized (cacheOrder) {
      while (textureCache.size() > MAX_CACHE_IMAGES && !cacheOrder.isEmpty()) {
        String evict = cacheOrder.pollFirst();
        if (evict != null) {
          PImage old = textureCache.remove(evict);
          // Help GC by clearing reference; Processing doesn't require explicit dispose for PImage
          old = null;
        }
      }
    }
  }
}

// Aggressively trim cache (used after OutOfMemoryError) retaining only most recent third
void emergencyCacheTrim() {
  synchronized (textureCache) {
    synchronized (cacheOrder) {
      int keep = cacheOrder.size() / 3; // keep newest third
      ArrayDeque<String> reversed = new ArrayDeque<String>();
      // copy to list to preserve order
      for (String name : cacheOrder) reversed.addLast(name);
      // determine survivors (tail elements)
      HashSet<String> survivors = new HashSet<String>();
      int skip = reversed.size() - keep;
      int idx = 0;
      for (String name : reversed) {
        if (idx++ >= skip) survivors.add(name);
      }
      // evict non-survivors
      Iterator<String> it = cacheOrder.iterator();
      while (it.hasNext()) {
        String n = it.next();
        if (!survivors.contains(n)) {
          it.remove();
          textureCache.remove(n);
        }
      }
    }
  }
  println("[cache] Emergency trim complete. Remaining textures: " + textureCache.size());
}

void drawMemoryStats() {
  Runtime rt = Runtime.getRuntime();
  long used = (rt.totalMemory() - rt.freeMemory()) / (1024 * 1024);
  long total = rt.totalMemory() / (1024 * 1024);
  long max = rt.maxMemory() / (1024 * 1024);
  fill(0, 160);
  noStroke();
  rect(8, 8, 320, 86);
  fill(255);
  textAlign(LEFT, TOP);
  text("Mem used: " + used + " MB\nTotal: " + total + " MB\nMax: " + max + " MB\nCache: " + textureCache.size() + "/" + MAX_CACHE_IMAGES + "\nQueue: " + loadQueue.size(), 16, 16);
}

void mousePressed() {
  if (!editMode) return;
  
  if (dragAllMode) {
    dragAllOffset.x = mouseX;
    dragAllOffset.y = mouseY;
    return;
  }
  
  for (int j = 0; j < rows; j++) {
    for (int i = 0; i < cols; i++) {
      if (dist(mouseX, mouseY, points[j][i].x, points[j][i].y) < dragThreshold) {
        draggedI = i;
        draggedJ = j;
        return;
      }
    }
  }
}

void mouseDragged() {
  if (dragAllMode) {
    float dx = mouseX - dragAllOffset.x;
    float dy = mouseY - dragAllOffset.y;
    
    for (int j = 0; j < rows; j++) {
      for (int i = 0; i < cols; i++) {
        points[j][i].x += dx;
        points[j][i].y += dy;
      }
    }
    
    dragAllOffset.x = mouseX;
    dragAllOffset.y = mouseY;
  } else if (draggedI != -1 && draggedJ != -1) {
    points[draggedJ][draggedI].x = mouseX;
    points[draggedJ][draggedI].y = mouseY;
  }
}

void mouseReleased() {
  draggedI = -1;
  draggedJ = -1;
}

void keyPressed() {
  if (key == 'r') resetPoints();
  if (key == 'e') editMode = !editMode;
  if (key == 'a') dragAllMode = !dragAllMode;

  // Save coordinates with Shift+S
  if (key == 'S') {
    saveCoordinates();
  }

  // Load coordinates with Shift+R
  if (key == 'R') {
    loadCoordinates();
  }

  // Scale mesh vertices around centroid
  if (key == '+') {
    scaleMesh(1.05); // scale up 5%
  }
  if (key == '-') {
    scaleMesh(0.95); // scale down 5%
  }
}

void saveCoordinates() {
  PrintWriter output = createWriter("mesh_coordinates.txt");
  output.println(rows + "," + cols);
  
  for (int j = 0; j < rows; j++) {
    for (int i = 0; i < cols; i++) {
      output.println(points[j][i].x + "," + points[j][i].y + "," + points[j][i].z);
    }
  }
  
  output.flush();
  output.close();
  println("Coordinates saved to mesh_coordinates.txt");
}

void loadCoordinates() {
  File f = new File(dataPath("mesh_coordinates.txt"));
  if (!f.exists()) {
    f = new File(sketchPath("mesh_coordinates.txt"));
  }
  
  if (!f.exists()) {
    println("No saved coordinates found");
    return;
  }
  
  String[] lines = loadStrings("mesh_coordinates.txt");
  if (lines.length < 1) {
    println("Invalid coordinate file");
    return;
  }
  
  String[] dimensions = split(lines[0], ',');
  int savedRows = int(dimensions[0]);
  int savedCols = int(dimensions[1]);
  
  if (savedRows != rows || savedCols != cols) {
    println("Warning: Saved dimensions don't match current mesh");
    return;
  }
  
  int lineIndex = 1;
  for (int j = 0; j < rows; j++) {
    for (int i = 0; i < cols; i++) {
      if (lineIndex < lines.length) {
        String[] coords = split(lines[lineIndex], ',');
        points[j][i].x = float(coords[0]);
        points[j][i].y = float(coords[1]);
        points[j][i].z = float(coords[2]);
        lineIndex++;
      }
    }
  }
  
  println("Coordinates loaded from mesh_coordinates.txt");
}

void scaleMesh(float factor) {
  // Compute centroid of all points
  float cx = 0, cy = 0, cz = 0;
  int count = rows * cols;
  for (int j = 0; j < rows; j++) {
    for (int i = 0; i < cols; i++) {
      cx += points[j][i].x;
      cy += points[j][i].y;
      cz += points[j][i].z;
    }
  }
  cx /= count;
  cy /= count;
  cz /= count;

  // Scale each point around centroid
  for (int j = 0; j < rows; j++) {
    for (int i = 0; i < cols; i++) {
      PVector p = points[j][i];
      p.x = cx + (p.x - cx) * factor;
      p.y = cy + (p.y - cy) * factor;
      p.z = cz + (p.z - cz) * factor;
    }
  }
}
