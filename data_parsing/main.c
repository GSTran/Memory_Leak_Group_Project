#include <stdio.h>
#include <string.h>
#include <stdlib.h>

void to_csv(const char* filename) {
    FILE *fp = fopen(filename, "r");
    FILE *fout = fopen("output.csv", "w");
    char line[4096];

    while (fgets(line, sizeof(line), fp)) {
        for (int i = 0; i < strlen(line); i++) {
            if (line[i] == '\t') {
                line[i] = ',';
            }
        }
        fprintf(fout, "%s", line);
    }

    fclose(fp);
    fclose(fout);
}

void to_json(const char* filename) {
    FILE *fp = fopen(filename, "r");
    FILE *fout = fopen("output.json", "w");
    char line[4096];
    char *token;

    fprintf(fout, "[\n");
    int first = 1;

    while (fgets(line, sizeof(line), fp)) {
        if (!first) {
            fprintf(fout, ",\n");
        }
        first = 0;

        fprintf(fout, "{\n");
        token = strtok(line, "\t\n");
        int col = 0;
        while (token != NULL) {
            fprintf(fout, "  \"col%d\": \"%s\"", col, token);
            token = strtok(NULL, "\t\n");
            if (token) {
                fprintf(fout, ",\n");
            }
            col++;
        }
        fprintf(fout, "\n}");
    }
    fprintf(fout, "\n]");

    fclose(fp);
    fclose(fout);
}

void to_xml(const char* filename) {
    FILE *fp = fopen(filename, "r");
    FILE *fout = fopen("output.xml", "w");
    char line[4096];
    char *token;

    fprintf(fout, "<data>\n");

    while (fgets(line, sizeof(line), fp)) {
        fprintf(fout, "  <row>\n");
        token = strtok(line, "\t\n");
        int col = 0;
        while (token != NULL) {
            fprintf(fout, "    <col%d>%s</col%d>\n", col, token, col);
            token = strtok(NULL, "\t\n");
            col++;
        }
        fprintf(fout, "  </row>\n");
    }
    fprintf(fout, "</data>");

    fclose(fp);
    fclose(fout);
}

int main(int argc, char *argv[]) {
    if (argc != 3) {
        printf("Usage: %s <filename> <format flag>\n", argv[0]);
        printf("Flags:\n");
        printf("-c   CSV format\n");
        printf("-j   JSON format\n");
        printf("-x   XML format\n");
        return 1;
    }

    if (strcmp(argv[2], "-c") == 0) {
        to_csv(argv[1]);
    } else if (strcmp(argv[2], "-j") == 0) {
        to_json(argv[1]);
    } else if (strcmp(argv[2], "-x") == 0) {
        to_xml(argv[1]);
    } else {
        printf("Invalid format flag. Use -c, -j, or -x.\n");
        return 1;
    }

    printf("Conversion completed successfully.\n");
    return 0;
}
