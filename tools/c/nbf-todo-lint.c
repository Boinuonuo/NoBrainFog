#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX_LINE 8192
#define MAX_TASKS 4096
#define MAX_TASK_TEXT 2048
#define COLUMN_COUNT 7

typedef struct {
    char text[MAX_TASK_TEXT];
    int line_number;
} TaskRecord;

typedef struct {
    unsigned long task_rows;
    unsigned long malformed_rows;
    unsigned long empty_tasks;
    unsigned long invalid_priorities;
    unsigned long duplicate_tasks;
} LintStats;

static char *trim(char *value) {
    char *end;

    while (isspace((unsigned char)*value)) {
        value++;
    }

    if (*value == '\0') {
        return value;
    }

    end = value + strlen(value) - 1;
    while (end > value && isspace((unsigned char)*end)) {
        end--;
    }

    *(end + 1) = '\0';
    return value;
}

static void strip_markdown_bold(char *value) {
    char *read_ptr = value;
    char *write_ptr = value;

    while (*read_ptr != '\0') {
        if (read_ptr[0] == '*' && read_ptr[1] == '*') {
            read_ptr += 2;
            continue;
        }
        *write_ptr = *read_ptr;
        write_ptr++;
        read_ptr++;
    }

    *write_ptr = '\0';
}

static void normalize_task_text(char *value) {
    char *read_ptr = value;
    char *write_ptr = value;
    int last_was_space = 0;

    while (*read_ptr != '\0') {
        unsigned char c = (unsigned char)*read_ptr;
        if (isspace(c)) {
            if (!last_was_space) {
                *write_ptr = ' ';
                write_ptr++;
                last_was_space = 1;
            }
        } else {
            *write_ptr = (char)tolower(c);
            write_ptr++;
            last_was_space = 0;
        }
        read_ptr++;
    }

    if (write_ptr > value && *(write_ptr - 1) == ' ') {
        write_ptr--;
    }

    *write_ptr = '\0';
}

static int starts_with_task_marker(const char *line) {
    const char *p = line;

    while (isspace((unsigned char)*p)) {
        p++;
    }

    return p[0] == '|' && isspace((unsigned char)p[1]) && p[2] == '[';
}

static int split_markdown_row(char *line, char *columns[], int max_columns) {
    int count = 0;
    char *cursor = line;
    char *token;

    if (*cursor == '|') {
        cursor++;
    }

    token = strtok(cursor, "|");
    while (token != NULL && count < max_columns) {
        columns[count] = trim(token);
        count++;
        token = strtok(NULL, "|");
    }

    return count;
}

static int is_valid_priority(char *priority) {
    strip_markdown_bold(priority);
    priority = trim(priority);

    return strcmp(priority, "P0") == 0 ||
           strcmp(priority, "P1") == 0 ||
           strcmp(priority, "P2") == 0 ||
           strcmp(priority, "P3") == 0 ||
           strcmp(priority, "") == 0;
}

static int find_duplicate(TaskRecord records[], int record_count, const char *task_text) {
    for (int i = 0; i < record_count; i++) {
        if (strcmp(records[i].text, task_text) == 0) {
            return records[i].line_number;
        }
    }
    return 0;
}

static void print_usage(const char *program_name) {
    fprintf(stderr, "Usage: %s /path/to/todo.md\n", program_name);
    fprintf(stderr, "Example: %s /root/nbf-vault/todo.md\n", program_name);
}

int main(int argc, char *argv[]) {
    FILE *file;
    char line[MAX_LINE];
    TaskRecord *records;
    LintStats stats = {0, 0, 0, 0, 0};
    int record_count = 0;
    int line_number = 0;
    int exit_code = 0;

    if (argc != 2) {
        print_usage(argv[0]);
        return 2;
    }

    records = calloc(MAX_TASKS, sizeof(TaskRecord));
    if (records == NULL) {
        fprintf(stderr, "Failed to allocate task records.\n");
        return 2;
    }

    file = fopen(argv[1], "r");
    if (file == NULL) {
        perror("Failed to open todo.md");
        free(records);
        return 2;
    }

    while (fgets(line, sizeof(line), file) != NULL) {
        char line_copy[MAX_LINE];
        char *columns[COLUMN_COUNT + 2];
        int column_total;

        line_number++;

        if (!starts_with_task_marker(line)) {
            continue;
        }

        stats.task_rows++;

        strncpy(line_copy, line, sizeof(line_copy) - 1);
        line_copy[sizeof(line_copy) - 1] = '\0';

        column_total = split_markdown_row(line_copy, columns, COLUMN_COUNT + 2);
        if (column_total < COLUMN_COUNT) {
            printf("Line %d: malformed task row, expected at least %d columns but found %d.\n",
                   line_number, COLUMN_COUNT, column_total);
            stats.malformed_rows++;
            continue;
        }

        if (strlen(columns[2]) == 0) {
            printf("Line %d: empty task description.\n", line_number);
            stats.empty_tasks++;
        }

        if (!is_valid_priority(columns[1])) {
            printf("Line %d: invalid priority '%s'. Expected P0, P1, P2, or P3.\n",
                   line_number, columns[1]);
            stats.invalid_priorities++;
        }

        if (strlen(columns[2]) > 0) {
            char normalized[MAX_TASK_TEXT];
            int duplicate_line;

            strncpy(normalized, columns[2], sizeof(normalized) - 1);
            normalized[sizeof(normalized) - 1] = '\0';
            normalize_task_text(normalized);

            duplicate_line = find_duplicate(records, record_count, normalized);
            if (duplicate_line > 0) {
                printf("Line %d: duplicate task description, first seen on line %d.\n",
                       line_number, duplicate_line);
                stats.duplicate_tasks++;
            } else if (record_count < MAX_TASKS) {
                strncpy(records[record_count].text, normalized, sizeof(records[record_count].text) - 1);
                records[record_count].text[sizeof(records[record_count].text) - 1] = '\0';
                records[record_count].line_number = line_number;
                record_count++;
            }
        }
    }

    fclose(file);

    printf("\nNoBrainFog todo lint summary\n");
    printf("----------------------------\n");
    printf("Task rows:          %lu\n", stats.task_rows);
    printf("Malformed rows:     %lu\n", stats.malformed_rows);
    printf("Empty tasks:        %lu\n", stats.empty_tasks);
    printf("Invalid priorities: %lu\n", stats.invalid_priorities);
    printf("Duplicate tasks:    %lu\n", stats.duplicate_tasks);

    if (stats.malformed_rows || stats.empty_tasks || stats.invalid_priorities || stats.duplicate_tasks) {
        printf("\nStatus: issues found.\n");
        exit_code = 1;
    } else {
        printf("\nStatus: clean. ✅\n");
        exit_code = 0;
    }

    free(records);
    return exit_code;
}
