#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX_USERS 100
#define MAX_ORDERS 500

typedef struct {
    char username[50];
    char email[50];
    char password[50];
    float balance;
} User;

typedef struct {
    int orderId;
    char username[50];
    char service[100];
    char link[200];
    int quantity;
    float price;
    char status[20];
} Order;

User users[MAX_USERS];
int userCount = 0;
Order orders[MAX_ORDERS];
int orderCount = 0;

int loggedInUserIndex = -1;

// Services List in PKR
const char* services[] = {
    "Instagram Followers [HQ] - Rs. 450 per 1000",
    "Instagram Likes [Instant] - Rs. 150 per 1000",
    "TikTok Views [Super Fast] - Rs. 30 per 1000",
    "TikTok Followers [Real] - Rs. 850 per 1000",
    "YouTube Subscribers [Lifetime] - Rs. 3500 per 1000"
};
float serviceRates[] = {450.0, 150.0, 30.0, 850.0, 3500.0};
int totalServices = 5;

void loadData() {
    FILE *fUser = fopen("users.txt", "r");
    if (fUser != NULL) {
        userCount = 0;
        while (fscanf(fUser, "%s %s %s %f", users[userCount].username, users[userCount].email, users[userCount].password, &users[userCount].balance) == 4) {
            userCount++;
            if (userCount >= MAX_USERS) break;
        }
        fclose(fUser);
    }

    FILE *fOrder = fopen("orders.txt", "r");
    if (fOrder != NULL) {
        orderCount = 0;
        while (fscanf(fOrder, "%d %s %s %s %d %f %s", &orders[orderCount].orderId, orders[orderCount].username, orders[orderCount].service, orders[orderCount].link, &orders[orderCount].quantity, &orders[orderCount].price, orders[orderCount].status) == 7) {
            orderCount++;
            if (orderCount >= MAX_ORDERS) break;
        }
        fclose(fOrder);
    }
}

void saveUsers() {
    FILE *fUser = fopen("users.txt", "w");
    if (fUser != NULL) {
        for (int i = 0; i < userCount; i++) {
            fprintf(fUser, "%s %s %s %.2f\n", users[i].username, users[i].email, users[i].password, users[i].balance);
        }
        fclose(fUser);
    }
}

void saveOrders() {
    FILE *fOrder = fopen("orders.txt", "w");
    if (fOrder != NULL) {
        for (int i = 0; i < orderCount; i++) {
            fprintf(fOrder, "%d %s %s %s %d %.2f %s\n", orders[i].orderId, orders[i].username, orders[i].service, orders[i].link, orders[i].quantity, orders[i].price, orders[i].status);
        }
        fclose(fOrder);
    }
}

void registerUser() {
    if (userCount >= MAX_USERS) {
        printf("\n[Error] Database full hai!\n");
        return;
    }
    User u;
    printf("\n--- Naya Account Banayein ---\n");
    printf("Username enter karein: ");
    scanf("%s", u.username);
    
    // Check if user exists
    for (int i = 0; i < userCount; i++) {
        if (strcmp(users[i].username, u.username) == 0) {
            printf("[Error] Yeh username pehle se mojood hai!\n");
            return;
        }
    }

    printf("Email enter karein: ");
    scanf("%s", u.email);
    printf("Password enter karein: ");
    scanf("%s", u.password);
    
    // Balance strictly 0.00 on signup (No free bonus)
    u.balance = 0.00;

    users[userCount] = u;
    userCount++;
    saveUsers();
    printf("\n[Success] Account kamyaabi se ban gaya hai! Ab balance Rs. 0.00 hai.\n");
}

void loginUser() {
    char uname[50], pass[50];
    printf("\n--- Login ---\n");
    printf("Username enter karein: ");
    scanf("%s", uname);
    printf("Password enter karein: ");
    scanf("%s", pass);

    for (int i = 0; i < userCount; i++) {
        if (strcmp(users[i].username, uname) == 0 && strcmp(users[i].password, pass) == 0) {
            loggedInUserIndex = i;
            printf("\n[Success] Welcome back, %s!\n", users[i].username);
            return;
        }
    }
    printf("\n[Error] Ghalat Username ya Password!\n");
}

void viewServices() {
    printf("\n--- Available SMM Services (PKR) ---\n");
    for (int i = 0; i < totalServices; i++) {
        printf("%d. %s\n", i + 1, services[i]);
    }
}

void placeOrder() {
    if (loggedInUserIndex == -1) return;

    viewServices();
    int choice, qty;
    char link[200];

    printf("\nService ka number select karein (1-%d): ", totalServices);
    scanf("%d", &choice);

    if (choice < 1 || choice > totalServices) {
        printf("[Error] Ghalat service select ki gayi hai!\n");
        return;
    }

    printf("Target Link enter karein: ");
    scanf("%s", link);
    printf("Quantity enter karein: ");
    scanf("%d", &qty);

    float totalPrice = (qty * serviceRates[choice - 1]) / 1000.0;

    if (users[loggedInUserIndex].balance < totalPrice) {
        printf("\n[Error] Balance kam hai! Aapka balance Rs. %.2f hai jabke order ki cost Rs. %.2f hai.\n", 
               users[loggedInUserIndex].balance, totalPrice);
        printf("Pehle Add Funds ke zariye balance update karein.\n");
        return;
    }

    // Deduct balance and create order
    users[loggedInUserIndex].balance -= totalPrice;
    
    Order o;
    o.orderId = orderCount + 1001;
    strcpy(o.username, users[loggedInUserIndex].username);
    strcpy(o.service, services[choice - 1]);
    strcpy(o.link, link);
    o.quantity = qty;
    o.price = totalPrice;
    strcpy(o.status, "In_Progress");

    orders[orderCount] = o;
    orderCount++;

    saveUsers();
    saveOrders();

    printf("\n[Success] Order kamyaabi se place ho gaya! Order ID: #%d, Total Cost: Rs. %.2f\n", o.orderId, totalPrice);
}

void viewOrders() {
    if (loggedInUserIndex == -1) return;

    printf("\n--- Aapke Orders ki History ---\n");
    int found = 0;
    for (int i = 0; i < orderCount; i++) {
        if (strcmp(orders[i].username, users[loggedInUserIndex].username) == 0) {
            printf("ID: #%d | Service: %s | Link: %s | Qty: %d | Cost: Rs. %.2f | Status: %s\n",
                   orders[i].orderId, orders[i].service, orders[i].link, orders[i].quantity, orders[i].price, orders[i].status);
            found = 1;
        }
    }
    if (!found) {
        printf("Aapne abhi tak koi order place nahi kiya.\n");
    }
}

void addFundsMenu() {
    if (loggedInUserIndex == -1) return;

    printf("\n--- Add Funds (Manual Method) ---\n");
    printf("Easypaisa / NayaPay / SadaPay Title: Arman Akhtar\n");
    printf("Account Number: 03281583582\n");
    printf("Raqam transfer karne ke baad admin se rabta karein taaki balance update ho.\n");
    
    int choice;
    printf("\nKya aap admin hain aur khud balance add karna chahte hain? (1. Haan / 2. Nahi): ");
    scanf("%d", &choice);
    if (choice == 1) {
        float amt;
        printf("Kitni rakam add karni hai? (Rs): ");
        scanf("%f", &amt);
        users[loggedInUserIndex].balance += amt;
        saveUsers();
        printf("[Success] Rs. %.2f kamyaabi se add ho gaye hain! Naya Balance: Rs. %.2f\n", amt, users[loggedInUserIndex].balance);
    }
}

void dashboard() {
    int choice;
    while (loggedInUserIndex != -1) {
        printf("\n====== SMM PANEL DASHBOARD (User: %s | Balance: Rs. %.2f) ======\n", 
               users[loggedInUserIndex].username, users[loggedInUserIndex].balance);
        printf("1. View Services\n");
        printf("2. Place New Order\n");
        printf("3. View Order History\n");
        printf("4. Add Funds Info / Manual Update\n");
        printf("5. Logout\n");
        printf("Apni choice enter karein: ");
        scanf("%d", &choice);

        switch (choice) {
            case 1:
                viewServices();
                break;
            case 2:
                placeOrder();
                break;
            case 3:
                viewOrders();
                break;
            case 4:
                addFundsMenu();
                break;
            case 5:
                loggedInUserIndex = -1;
                printf("[Info] Logged out successfully.\n");
                return;
            default:
                printf("[Error] Ghalat choice! Dobara koshish karein.\n");
        }
    }
}

int main() {
    loadData();
    int choice;
    while (1) {
        printf("\n========== ARMAN SMM PANEL (C LANGUAGE) ==========\n");
        printf("1. Login\n");
        printf("2. Sign Up (Naya Account)\n");
        printf("3. Exit\n");
        printf("Apni choice enter karein: ");
        scanf("%d", &choice);

        switch (choice) {
            case 1:
                loginUser();
                if (loggedInUserIndex != -1) {
                    dashboard();
                }
                break;
            case 2:
                registerUser();
                break;
            case 3:
                printf("Program band ho raha hai. Allah Hafiz!\n");
                exit(0);
            default:
                printf("[Error] Ghalat choice! Dobara koshish karein.\n");
        }
    }
    return 0;
}
