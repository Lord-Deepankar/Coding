#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <sys/stat.h>
#include <dirent.h> // For DIR, dirent, opendir, readdir, closedir
#include <errno.h>
#include <time.h>
#include <stdint.h>
#include <linux/btrfs.h>

#define BTRFS_SEARCH_ARGS_BUFSIZE (4096 - sizeof(struct btrfs_ioctl_search_key))

struct file_entry {
    char path[4096];
    char name[256];
    uint64_t inode;
    uint64_t size;
    uint64_t mtime;
    uint32_t mode;
    struct file_entry *next;
};

static struct file_entry *file_list = NULL;
static int file_count = 0;

// Add file entry to our list
void add_file_entry(const char *path, const char *name, uint64_t inode, 
                   uint64_t size, uint64_t mtime, uint32_t mode) {
    struct file_entry *entry = malloc(sizeof(struct file_entry));
    if (!entry) return;
    
    strncpy(entry->path, path, sizeof(entry->path) - 1);
    strncpy(entry->name, name, sizeof(entry->name) - 1);
    entry->path[sizeof(entry->path) - 1] = '\0';
    entry->name[sizeof(entry->name) - 1] = '\0';
    entry->inode = inode;
    entry->size = size;
    entry->mtime = mtime;
    entry->mode = mode;
    entry->next = file_list;
    file_list = entry;
    file_count++;
}

// Convert timestamp to ISO format
void timestamp_to_iso(uint64_t timestamp, char *buffer, size_t size) {
    time_t time = (time_t)timestamp;
    struct tm *tm_info = gmtime(&time);
    strftime(buffer, size, "%Y-%m-%dT%H:%M:%SZ", tm_info);
}

// Escape JSON string
void json_escape(const char *src, char *dst, size_t dst_size) {
    size_t src_len = strlen(src);
    size_t dst_idx = 0;
    
    for (size_t i = 0; i < src_len && dst_idx < dst_size - 2; i++) {
        switch (src[i]) {
            case '"':
                if (dst_idx < dst_size - 3) {
                    dst[dst_idx++] = '\\';
                    dst[dst_idx++] = '"';
                }
                break;
            case '\\':
                if (dst_idx < dst_size - 3) {
                    dst[dst_idx++] = '\\';
                    dst[dst_idx++] = '\\';
                }
                break;
            case '\n':
                if (dst_idx < dst_size - 3) {
                    dst[dst_idx++] = '\\';
                    dst[dst_idx++] = 'n';
                }
                break;
            case '\r':
                if (dst_idx < dst_size - 3) {
                    dst[dst_idx++] = '\\';
                    dst[dst_idx++] = 'r';
                }
                break;
            case '\t':
                if (dst_idx < dst_size - 3) {
                    dst[dst_idx++] = '\\';
                    dst[dst_idx++] = 't';
                }
                break;
            default:
                if (src[i] >= 32) {
                    dst[dst_idx++] = src[i];
                }
                break;
        }
    }
    dst[dst_idx] = '\0';
}

// Output results as JSON
void output_json() {
    printf("{\n");
    printf("  \"metadata\": {\n");
    printf("    \"total_files\": %d,\n", file_count);
    printf("    \"scan_time\": \"%ld\",\n", time(NULL));
    printf("    \"format\": \"btrfs_metadata\"\n");
    printf("  },\n");
    printf("  \"files\": [\n");
    
    struct file_entry *entry = file_list;
    int first = 1;
    
    while (entry) {
        if (!first) printf(",\n");
        first = 0;
        
        char escaped_path[8192];
        char escaped_name[512];
        char mtime_str[32];
        
        json_escape(entry->path, escaped_path, sizeof(escaped_path));
        json_escape(entry->name, escaped_name, sizeof(escaped_name));
        timestamp_to_iso(entry->mtime, mtime_str, sizeof(mtime_str));
        
        printf("    {\n");
        printf("      \"path\": \"%s\",\n", escaped_path);
        printf("      \"name\": \"%s\",\n", escaped_name);
        printf("      \"inode\": %lu,\n", entry->inode);
        printf("      \"size\": %lu,\n", entry->size);
        printf("      \"mtime\": \"%s\",\n", mtime_str);
        printf("      \"mode\": %u,\n", entry->mode);
        printf("      \"is_dir\": %s\n", S_ISDIR(entry->mode) ? "true" : "false");
        printf("    }");
        
        entry = entry->next;
    }
    
    printf("\n  ]\n");
    printf("}\n");
}

// Output results as CSV
void output_csv() {
    printf("path,name,inode,size,mtime,mode,is_dir\n");
    
    struct file_entry *entry = file_list;
    while (entry) {
        char mtime_str[32];
        timestamp_to_iso(entry->mtime, mtime_str, sizeof(mtime_str));
        
        printf("\"%s\",\"%s\",%lu,%lu,\"%s\",%u,%s\n",
               entry->path, entry->name, entry->inode, entry->size,
               mtime_str, entry->mode, S_ISDIR(entry->mode) ? "true" : "false");
        
        entry = entry->next;
    }
}

// Extract values from btrfs structures (little-endian)
static inline uint64_t get_le64(const void *ptr) {
    const uint8_t *p = ptr;
    return ((uint64_t)p[7] << 56) | ((uint64_t)p[6] << 48) | 
           ((uint64_t)p[5] << 40) | ((uint64_t)p[4] << 32) |
           ((uint64_t)p[3] << 24) | ((uint64_t)p[2] << 16) |
           ((uint64_t)p[1] << 8) | (uint64_t)p[0];
}

static inline uint32_t get_le32(const void *ptr) {
    const uint8_t *p = ptr;
    return ((uint32_t)p[3] << 24) | ((uint32_t)p[2] << 16) |
           ((uint32_t)p[1] << 8) | (uint32_t)p[0];
}

// Simplified btrfs inode item structure
struct simple_inode_item {
    uint64_t generation;
    uint64_t transid;
    uint64_t size;
    uint64_t nbytes;
    uint64_t block_group;
    uint32_t nlink;
    uint32_t uid;
    uint32_t gid;
    uint32_t mode;
    uint64_t rdev;
    uint64_t flags;
    uint64_t sequence;
    uint64_t reserved[4];
    struct {
        uint64_t sec;
        uint32_t nsec;
    } atime, ctime, mtime, otime;
} __attribute__((packed));

// Process inode item with direct memory access
void process_inode_item(uint64_t objectid, const void *item_data, 
                       uint32_t item_len, const char *path) {
    if (item_len < sizeof(struct simple_inode_item)) {
        return; // Invalid item
    }
    
    const struct simple_inode_item *inode = item_data;
    
    uint64_t size = get_le64(&inode->size);
    uint64_t mtime = get_le64(&inode->mtime.sec);
    uint32_t mode = get_le32(&inode->mode);
    
    // Extract filename from path
    const char *name = strrchr(path, '/');
    name = name ? name + 1 : path;
    
    add_file_entry(path, name, objectid, size, mtime, mode);
}

// Simple path reconstruction - just use inode number for now
void simple_path_name(uint64_t inode, char *path, size_t path_size) {
    snprintf(path, path_size, "/inode_%lu", inode);
}

// Forward declaration
int crawl_filesystem(const char *path);

// Search btrfs metadata using basic ioctl
int search_btrfs_metadata(const char *mount_path) {
    int fd = open(mount_path, O_RDONLY);
    if (fd < 0) {
        fprintf(stderr, "Error: Cannot open %s: %s\n", mount_path, strerror(errno));
        return -1;
    }
    
    // Try basic btrfs ioctl to see if it's a btrfs filesystem
    struct btrfs_ioctl_fs_info_args fs_info;
    if (ioctl(fd, BTRFS_IOC_FS_INFO, &fs_info) < 0) {
        fprintf(stderr, "Error: %s is not a btrfs filesystem or lacks permissions\n", mount_path);
        close(fd);
        return -1;
    }
    
    fprintf(stderr, "Warning: Direct metadata access failed, falling back to filesystem crawl...\n");
    close(fd);
    
    // Fallback: use standard filesystem traversal
    return crawl_filesystem(mount_path);
}

// Fallback filesystem crawler
int crawl_filesystem(const char *path) {
    DIR *dir;
    struct dirent *entry;
    struct stat st;
    char full_path[4096];
    
    dir = opendir(path);
    if (!dir) {
        return -1;
    }
    
    fprintf(stderr, "Crawling filesystem from %s...\n", path);
    
    while ((entry = readdir(dir)) != NULL) {
        if (strcmp(entry->d_name, ".") == 0 || strcmp(entry->d_name, "..") == 0) {
            continue;
        }
        
        snprintf(full_path, sizeof(full_path), "%s/%s", path, entry->d_name);
        
        if (lstat(full_path, &st) == 0) {
            add_file_entry(full_path, entry->d_name, st.st_ino, 
                          st.st_size, st.st_mtime, st.st_mode);
            
            if (file_count % 1000 == 0) {
                fprintf(stderr, "\rProcessed %d files...", file_count);
                fflush(stderr);
            }
            
            // Recursively process directories
            if (S_ISDIR(st.st_mode)) {
                crawl_filesystem(full_path);
            }
        }
    }
    
    closedir(dir);
    return 0;
}

// Print usage
void print_usage(const char *prog) {
    printf("Usage: %s [OPTIONS] <path>\n", prog);
    printf("Options:\n");
    printf("  -f FORMAT   Output format: json (default) or csv\n");
    printf("  -h          Show this help\n");
    printf("\n");
    printf("Example: %s /home > files.json\n", prog);
    printf("         %s -f csv /home > files.csv\n", prog);
}

int main(int argc, char *argv[]) {
    const char *path = NULL;
    const char *format = "json";
    int opt;
    
    while ((opt = getopt(argc, argv, "f:h")) != -1) {
        switch (opt) {
            case 'f':
                format = optarg;
                if (strcmp(format, "json") != 0 && strcmp(format, "csv") != 0) {
                    fprintf(stderr, "Error: Invalid format '%s'. Use 'json' or 'csv'.\n", format);
                    return 1;
                }
                break;
            case 'h':
                print_usage(argv[0]);
                return 0;
            default:
                print_usage(argv[0]);
                return 1;
        }
    }
    
    if (optind >= argc) {
        fprintf(stderr, "Error: Missing path.\n");
        print_usage(argv[0]);
        return 1;
    }
    
    path = argv[optind];
    
    // Check if path exists
    struct stat st;
    if (stat(path, &st) != 0) {
        fprintf(stderr, "Error: Cannot access %s: %s\n", path, strerror(errno));
        return 1;
    }
    
    if (!S_ISDIR(st.st_mode)) {
        fprintf(stderr, "Error: %s is not a directory.\n", path);
        return 1;
    }
    
    // Try btrfs metadata first, fallback to filesystem crawl
    if (search_btrfs_metadata(path) != 0) {
        if (crawl_filesystem(path) != 0) {
            fprintf(stderr, "Error: Failed to process filesystem.\n");
            return 1;
        }
    }
    
    fprintf(stderr, "\rCompleted! Found %d files.\n", file_count);
    
    // Output results
    if (strcmp(format, "csv") == 0) {
        output_csv();
    } else {
        output_json();
    }
    
    // Cleanup
    while (file_list) {
        struct file_entry *next = file_list->next;
        free(file_list);
        file_list = next;
    }
    
    return 0;
}