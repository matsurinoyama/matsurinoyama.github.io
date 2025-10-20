import java.util.*;

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
int imageChangeInterval = 2500; // 2.5 seconds

// Newest / hold behavior
String currentNewestName = null;
String pendingNewestName = null;
long pendingDetectedAt = 0;
long newestHoldUntil = 0;
int newestHoldDuration = 15000; // 15 second hold
int newFileDisplayDelay = 5000; // 5 seconds before showing a newly detected file

HashMap<String, PImage> textureCache = new HashMap<String, PImage>();
HashMap<String, Long> mtimes = new HashMap<String, Long>();
ArrayList<String> loadQueue = new ArrayList<String>(); // absolute paths
long lastPoll = 0;

// Crossfade / transition state
boolean transitioning = false;
int transitionDuration = 7500; // ms, tune for performance
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
            PImage loaded = loadImage(nextFile);
            if (loaded != null) {
              String name = new File(nextFile).getName();
              synchronized (textureCache) {
                textureCache.put(name, loaded);
              }
              println("[loader] loaded -> " + name + " (bytes=" + (loaded.width * loaded.height) + ")");
              // If this is the currently selected image, update img reference
              String currentName = getCurrentImageName();
              if (currentName != null && currentName.equals(name)) {
                synchronized (textureCache) {
                  img = textureCache.get(name);
                }
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
      String name = file.getName().toLowerCase();
      if (name.startsWith("aligned_") && (name.endsWith(".jpg") || name.endsWith(".png") || name.endsWith(".jpeg"))) {
        imageFiles.add(file.getAbsolutePath());
      }
    }
    Collections.sort(imageFiles);
  }
  if (imageFiles.size() > 0) {
    println("Found " + imageFiles.size() + " images in " + WATCH_DIR);
  }
}

// Return the filename (not path) of the currently selected image, or null
String getCurrentImageName() {
  if (imageFiles == null || imageFiles.size() == 0) return null;
  if (currentImageIndex < 0 || currentImageIndex >= imageFiles.size()) return null;
  return new File(imageFiles.get(currentImageIndex)).getName();
}


void pollFolderAndQueueLoads() {
  // Refresh imageFiles (absolute paths)
  loadImageFiles();

  // Tracks current filenames present
  HashSet<String> currentNames = new HashSet<String>();
  if (imageFiles != null) {
    for (String abs : imageFiles) {
      File f = new File(abs);
      String name = f.getName();
      currentNames.add(name);
      long mtime = f.lastModified();
      Long known = mtimes.get(name);
      // detect newest file by modification time
      if (currentNewestName == null) currentNewestName = name;
      try {
        File curNewest = new File(new File(imageFiles.get(0)).getAbsolutePath());
      } catch (Exception e) {}
      // update currentNewestName based on mtime
      String candidate = currentNewestName;
      long candidateTime = -1;
      try {
        if (currentNewestName != null) {
          for (String a : imageFiles) {
            long mt = new File(a).lastModified();
            if (mt > candidateTime) {
              candidateTime = mt;
              candidate = new File(a).getName();
            }
          }
        }
      } catch (Exception e) {}
      if (candidate != null && !candidate.equals(currentNewestName)) {
        // a new newest file appeared
        if (pendingNewestName == null || !pendingNewestName.equals(candidate)) {
          pendingNewestName = candidate;
          pendingDetectedAt = millis();
          println("[poll] pending newest -> " + pendingNewestName + " at " + pendingDetectedAt);
        }
      }
      if (known == null || known.longValue() != mtime) {
        mtimes.put(name, mtime);
        synchronized (loadQueue) {
          // avoid duplicate enqueues
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

  // Change image every interval if there are images
  // Special handling for newest/pending-new behavior
  // If we have a pendingNewestName and 20s have passed, show it immediately and hold for newestHoldDuration
  if (pendingNewestName != null) {
    if (millis() - pendingDetectedAt >= newFileDisplayDelay) {
      // set as current
      currentNewestName = pendingNewestName;
      pendingNewestName = null;
      newestHoldUntil = millis() + newestHoldDuration;
      // find and display it (if loaded)
      synchronized (textureCache) {
        if (textureCache.containsKey(currentNewestName)) {
          beginTransition(textureCache.get(currentNewestName));
          // update currentImageIndex to the index of this file if present
          for (int i = 0; i < imageFiles.size(); i++) {
            if (new File(imageFiles.get(i)).getName().equals(currentNewestName)) {
              currentImageIndex = i;
              break;
            }
          }
        }
      }
      lastImageChange = millis();
    }
  } else {
    // If we're currently holding the newest, keep it until newestHoldUntil
    if (millis() < newestHoldUntil) {
      // do nothing; keep displaying currentNewestName
    } else {
      // normal cycling behavior
      if (millis() - lastImageChange > imageChangeInterval && imageFiles != null && imageFiles.size() > 0) {
        int nextIndex = (currentImageIndex + 1) % imageFiles.size();
        String nextName = new File(imageFiles.get(nextIndex)).getName();
        synchronized (textureCache) {
          if (textureCache.containsKey(nextName)) {
            // start transition
            beginTransition(textureCache.get(nextName));
            currentImageIndex = nextIndex;
          } else {
            // queue load (absolute path)
            String abs = imageFiles.get(nextIndex);
            synchronized (loadQueue) { if (!loadQueue.contains(abs)) loadQueue.add(abs); }
            // keep previous img until new arrives
          }
        }
        lastImageChange = millis();
      }
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
